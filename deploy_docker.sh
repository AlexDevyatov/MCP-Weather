#!/usr/bin/env bash
#
# Deploy MCPWeather via plain Docker (no docker-compose needed).
#
# Usage examples:
#   ./deploy_docker.sh up --port 9001
#   ./deploy_docker.sh up --port 9001 --host 0.0.0.0 --no-cache
#   ./deploy_docker.sh logs
#   ./deploy_docker.sh status
#   ./deploy_docker.sh down
#
# Notes:
# - The MCP SSE endpoint will be:  http://<host>:<port>/sse
# - Health check:                 http://<host>:<port>/health
#
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DEFAULT_PORT="${SERVER_PORT:-9001}"
DEFAULT_HOST="${SERVER_HOST:-0.0.0.0}"
DEFAULT_CONTAINER_NAME="${CONTAINER_NAME:-mcp-weather}"
DEFAULT_IMAGE_NAME="${IMAGE_NAME:-mcp-weather:local}"

cmd="${1:-up}"
shift || true

PORT="$DEFAULT_PORT"
HOST="$DEFAULT_HOST"
CONTAINER_NAME="$DEFAULT_CONTAINER_NAME"
IMAGE_NAME="$DEFAULT_IMAGE_NAME"
NO_CACHE="false"
FOLLOW_LOGS="false"

usage() {
  cat <<'EOF'
deploy_docker.sh — deploy MCPWeather in Docker

Commands:
  up        Build image (optional) and run container (default)
  down      Stop & remove the container
  logs      Show container logs (-f)
  status    Show container status

Options (for "up"):
  --port <p>         Host/container port (default: 9001 or $SERVER_PORT)
  --host <h>         Host bind passed to server_remote.py (default: 0.0.0.0 or $SERVER_HOST)
  --name <n>         Container name (default: mcp-weather or $CONTAINER_NAME)
  --image <i>        Image name (default: mcp-weather:local or $IMAGE_NAME)
  --no-cache         Build without Docker cache
  --logs             Follow logs after start

Environment variables:
  SERVER_PORT, SERVER_HOST, CONTAINER_NAME, IMAGE_NAME

Examples:
  ./deploy_docker.sh up --port 9001 --no-cache --logs
  SERVER_PORT=9001 ./deploy_docker.sh up
  ./deploy_docker.sh down
EOF
}

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "ERROR: '$1' is required but not found in PATH" >&2
    exit 1
  fi
}

port_in_use() {
  local p="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -nP -iTCP:"$p" -sTCP:LISTEN >/dev/null 2>&1
    return $?
  fi
  if command -v ss >/dev/null 2>&1; then
    ss -ltn | awk '{print $4}' | grep -E "(:|\\])${p}\$" >/dev/null 2>&1
    return $?
  fi
  if command -v netstat >/dev/null 2>&1; then
    netstat -an 2>/dev/null | grep -E "LISTEN.*[\\.:]${p}[[:space:]]" >/dev/null 2>&1
    return $?
  fi
  return 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --port)
      PORT="${2:-}"
      shift 2
      ;;
    --host)
      HOST="${2:-}"
      shift 2
      ;;
    --name)
      CONTAINER_NAME="${2:-}"
      shift 2
      ;;
    --image)
      IMAGE_NAME="${2:-}"
      shift 2
      ;;
    --no-cache)
      NO_CACHE="true"
      shift
      ;;
    --logs)
      FOLLOW_LOGS="true"
      shift
      ;;
    *)
      echo "ERROR: Unknown option: $1" >&2
      echo "" >&2
      usage >&2
      exit 2
      ;;
  esac
done

need_cmd docker

if [[ "$cmd" == "down" ]]; then
  echo "Stopping/removing container: ${CONTAINER_NAME}"
  docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
  echo "Done."
  exit 0
fi

if [[ "$cmd" == "logs" ]]; then
  docker logs -f "${CONTAINER_NAME}"
  exit 0
fi

if [[ "$cmd" == "status" ]]; then
  docker ps -a --filter "name=^/${CONTAINER_NAME}$" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}"
  exit 0
fi

if [[ "$cmd" != "up" ]]; then
  echo "ERROR: Unknown command: $cmd" >&2
  echo "" >&2
  usage >&2
  exit 2
fi

if [[ -z "${PORT}" ]]; then
  echo "ERROR: --port is required" >&2
  exit 2
fi

if [[ "${PORT}" == "8000" ]]; then
  echo "ERROR: Port 8000 is not allowed. Choose another port (e.g. 9001)." >&2
  exit 2
fi

if port_in_use "${PORT}"; then
  echo "ERROR: Port ${PORT} is already in use on the host." >&2
  exit 1
fi

echo "=== MCPWeather Docker deploy ==="
echo "Project dir:     ${PROJECT_DIR}"
echo "Image:           ${IMAGE_NAME}"
echo "Container:       ${CONTAINER_NAME}"
echo "SERVER_HOST:     ${HOST}"
echo "SERVER_PORT:     ${PORT}"
echo ""

echo "Building image..."
build_args=()
if [[ "${NO_CACHE}" == "true" ]]; then
  build_args+=(--no-cache)
fi
docker build "${build_args[@]}" -t "${IMAGE_NAME}" "${PROJECT_DIR}"

echo "Removing existing container (if any)..."
docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true

echo "Starting container..."
docker run -d \
  --name "${CONTAINER_NAME}" \
  --restart unless-stopped \
  -e "SERVER_HOST=${HOST}" \
  -e "SERVER_PORT=${PORT}" \
  -p "${PORT}:${PORT}" \
  "${IMAGE_NAME}" >/dev/null

echo "Waiting for health check..."
for i in {1..30}; do
  if curl -fsS "http://localhost:${PORT}/health" >/dev/null 2>&1; then
    echo "✅ Healthy"
    echo "SSE endpoint:    http://localhost:${PORT}/sse"
    echo "Messages endpoint: http://localhost:${PORT}/messages/"
    break
  fi
  sleep 1
  if [[ "$i" == "30" ]]; then
    echo "⚠️  Health check did not pass in time. See logs:" >&2
    docker logs "${CONTAINER_NAME}" >&2 || true
    exit 1
  fi
done

if [[ "${FOLLOW_LOGS}" == "true" ]]; then
  echo ""
  echo "Following logs (Ctrl+C to stop watching)..."
  docker logs -f "${CONTAINER_NAME}"
fi


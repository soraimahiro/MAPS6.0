#!/bin/bash
# MAPS6 Raspberry Pi Control & Startup Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${SCRIPT_DIR}/data"
CONTAINER_NAME="maps6-nbiot-wifi"
IMAGE_NAME="maps6_v700:latest"
TAR_FILE="${SCRIPT_DIR}/maps6_v700.tar"

stop_system() {
    echo "Stopping MAPS6 container..."
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
    echo "MAPS6 container stopped."
}

load_image_if_missing() {
    if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
        if [ -f "$TAR_FILE" ]; then
            echo "Image $IMAGE_NAME not found. Loading from $TAR_FILE..."
            docker load -i "$TAR_FILE"
        else
            echo "Error: Image $IMAGE_NAME not found and $TAR_FILE does not exist."
            exit 1
        fi
    fi
}

start_system() {
    echo "=========================================="
    echo "Starting MAPS6 System..."
    echo "=========================================="

    load_image_if_missing
    mkdir -p "$DATA_DIR"
    docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

    docker run -itd --restart unless-stopped \
        --net=host \
        --name "$CONTAINER_NAME" \
        --privileged \
        -v /etc/localtime:/etc/localtime:ro \
        -v "$DATA_DIR":/mnt/SD \
        "$IMAGE_NAME"

    sleep 2
    STATUS=$(docker inspect -f '{{.State.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo "unknown")
    IP=$(hostname -I | awk '{print $1}')
    if [ -z "$IP" ]; then
        IP="localhost"
    fi

    echo ""
    echo "MAPS6 container status: $STATUS"
    echo "Data directory: $DATA_DIR"
    echo "Web dashboard: http://${IP}:5000"
    echo "View logs: docker logs $CONTAINER_NAME -f"
    echo "=========================================="
}

case "$1" in
    stop)
        stop_system
        ;;
    reload|reload-image|update)
        stop_system
        load_image
        start_system
        ;;
    restart)
        stop_system
        start_system
        ;;
    logs)
        docker logs "$CONTAINER_NAME" -f
        ;;
    start|*)
        start_system
        ;;
esac

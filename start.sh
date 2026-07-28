#!/bin/bash
# MAPS6 Raspberry Pi Control & Startup Script

DATA_DIR="/home/pi/MAPS6_system/data"
CONTAINER_NAME="maps6-nbiot-wifi"
IMAGE_NAME="maps6_v700:latest"
TAR_FILE="maps6_v700.tar"

stop_system() {
    echo "Stopping MAPS6 container..."
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
    echo "MAPS6 container stopped."
}

load_image() {
    if [ -f "$TAR_FILE" ]; then
        echo "Loading docker image from $TAR_FILE..."
        docker load -i "$TAR_FILE"
    else
        echo "Warning: $TAR_FILE not found in current directory."
    fi
}

start_system() {
    echo "=========================================="
    echo "Starting MAPS6 System..."
    echo "=========================================="

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
    reload|reload-image)
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
    *)
        if [ -f "$TAR_FILE" ]; then
            load_image
        fi
        start_system
        ;;
esac

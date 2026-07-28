#!/bin/bash
# MAPS6 Raspberry Pi Startup Script

DATA_DIR="/home/pi/MAPS6_system/data"

echo "=========================================="
echo "Starting MAPS6 System..."
echo "=========================================="

if [ -f "maps6_v700.tar" ]; then
    echo "Loading docker image from maps6_v700.tar..."
    docker load -i maps6_v700.tar
fi

mkdir -p "$DATA_DIR"
docker rm -f maps6-nbiot-wifi 2>/dev/null || true

docker run -itd --restart unless-stopped \
    --net=host \
    --name maps6-nbiot-wifi \
    --privileged \
    -v /etc/localtime:/etc/localtime:ro \
    -v "$DATA_DIR":/mnt/SD \
    maps6_v700:latest

# 取得容器狀態與本機 IP
sleep 2
STATUS=$(docker inspect -f '{{.State.Status}}' maps6-nbiot-wifi 2>/dev/null || echo "unknown")
IP=$(hostname -I | awk '{print $1}')
if [ -z "$IP" ]; then
    IP="localhost"
fi

echo ""
echo "MAPS6 container status: $STATUS"
echo "Data directory: $DATA_DIR"
echo "Web dashboard: http://${IP}:5000"
echo "View logs: docker logs maps6-nbiot-wifi -f"
echo "=========================================="

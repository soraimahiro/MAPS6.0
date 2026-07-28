#!/bin/bash
# MAPS6 Raspberry Pi Startup Script

DATA_DIR="/home/pi/maps6_data"

echo "=========================================="
echo "Starting MAPS6 System..."
echo "=========================================="

mkdir -p "$DATA_DIR"
docker rm -f maps6-nbiot-wifi 2>/dev/null || true

docker run -itd --restart unless-stopped \
    --net=host \
    --name maps6-nbiot-wifi \
    --privileged \
    -v /etc/localtime:/etc/localtime:ro \
    -v "$DATA_DIR":/mnt/SD \
    maps6_v700:latest

echo ""
echo "MAPS6 container started successfully."
echo "Data directory: $DATA_DIR"
echo "Web dashboard: http://<RaspberryPi-IP>:5000"
echo "View logs: docker logs maps6-nbiot-wifi -f"
echo "=========================================="

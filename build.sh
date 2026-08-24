#!/bin/bash
set -e

# ==============================================================================
# MAPS6 Docker Cross-Compilation & Deployment Script
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="maps6_v700:latest"
TAR_FILE="${SCRIPT_DIR}/maps6_v700.tar"
PLATFORM="linux/arm/v7"

show_help() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  build                  Build docker image for ARMv7 and export to tar"
    echo "  push-pi <pi_host>      Build and transfer (tar + start.sh) to Raspberry Pi"
    echo "                         Example: $0 push-pi pi@192.168.1.100"
    echo "  split                  Split tar file into 30MB chunks for unstable network"
    echo "  clean                  Remove generated .tar file and split chunks"
    echo "  help                   Show this help message"
    echo ""
}

cmd_build() {
    echo "=================================================="
    echo "Building Docker image for ${PLATFORM}..."
    echo "Target output: ${TAR_FILE}"
    echo "=================================================="
    
    docker buildx build \
        --platform "${PLATFORM}" \
        -t "${IMAGE_NAME}" \
        --output type=docker,dest="${TAR_FILE}" \
        "${SCRIPT_DIR}"
        
    echo ""
    echo "Build success! Output file: ${TAR_FILE}"
    ls -lh "${TAR_FILE}"
}

cmd_push_pi() {
    local TARGET_HOST="$1"
    if [ -z "${TARGET_HOST}" ]; then
        echo "Error: Missing target host. Usage: $0 push-pi <user@host> [remote_dir]"
        exit 1
    fi
    local REMOTE_DIR="${2:-/home/pi/}"

    if [ ! -f "${TAR_FILE}" ]; then
        echo "Tar file not found, building first..."
        cmd_build
    fi

    echo "=================================================="
    echo "Deploying to ${TARGET_HOST}:${REMOTE_DIR}..."
    echo "=================================================="

    rsync -avzP "${TAR_FILE}" "${SCRIPT_DIR}/start.sh" "${TARGET_HOST}:${REMOTE_DIR}"
    
    echo "Transfer complete!"
    echo "To start on Pi, run: ssh ${TARGET_HOST} 'cd ${REMOTE_DIR} && ./start.sh reload'"
}

cmd_split() {
    if [ ! -f "${TAR_FILE}" ]; then
        echo "Error: ${TAR_FILE} not found. Run './build.sh build' first."
        exit 1
    fi
    echo "Splitting ${TAR_FILE} into 30MB chunks..."
    rm -f "${SCRIPT_DIR}"/maps6_part_*
    split -b 30m "${TAR_FILE}" "${SCRIPT_DIR}/maps6_part_"
    echo "Split complete! Chunks:"
    ls -lh "${SCRIPT_DIR}"/maps6_part_*
}

cmd_clean() {
    echo "Cleaning up build artifacts..."
    rm -f "${TAR_FILE}" "${SCRIPT_DIR}"/maps6_part_*
    echo "Clean complete."
}

case "$1" in
    build)
        cmd_build
        ;;
    push-pi|deploy)
        shift
        cmd_push_pi "$@"
        ;;
    split)
        cmd_split
        ;;
    clean)
        cmd_clean
        ;;
    help|--help|-h|"")
        if [ "$1" = "" ]; then
            cmd_build
        else
            show_help
        fi
        ;;
    *)
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac

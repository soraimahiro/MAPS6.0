# ==============================================================================
# MAPS6 Build Makefile
# ==============================================================================

IMAGE_NAME   ?= maps6_v700:latest
PLATFORM     ?= linux/arm/v7
TAR_FILE     ?= maps6_v700.tar
REMOTE_DIR   ?= /home/pi/

.PHONY: all build push-pi split clean help

all: build

## help: Show this help message
help:
	@echo "Usage: make [target] [PI_HOST=user@ip]"
	@echo ""
	@echo "Targets:"
	@echo "  build         Build Docker image for ARMv7 and export to $(TAR_FILE)"
	@echo "  push-pi       Build & transfer $(TAR_FILE) + start.sh to Raspberry Pi (requires PI_HOST)"
	@echo "                Example: make push-pi PI_HOST=pi@192.168.1.100"
	@echo "  split         Split $(TAR_FILE) into 30MB chunks"
	@echo "  clean         Remove generated $(TAR_FILE) and chunks"
	@echo ""

## build: Build docker image for ARMv7
build:
	@echo "==> Building Docker image for $(PLATFORM)..."
	docker buildx build \
		--platform $(PLATFORM) \
		-t $(IMAGE_NAME) \
		--output type=docker,dest=$(TAR_FILE) \
		.
	@echo "==> Build complete: $(TAR_FILE)"
	@ls -lh $(TAR_FILE)

## push-pi: Deploy tar and start.sh to Raspberry Pi
push-pi: build
	@if [ -z "$(PI_HOST)" ]; then \
		echo "Error: PI_HOST is not set. Example: make push-pi PI_HOST=pi@192.168.1.100"; \
		exit 1; \
	fi
	@echo "==> Deploying to $(PI_HOST):$(REMOTE_DIR)..."
	rsync -avzP $(TAR_FILE) start.sh $(PI_HOST):$(REMOTE_DIR)
	@echo "==> Transfer complete!"

## split: Split tar file into 30MB parts
split: $(TAR_FILE)
	@echo "==> Splitting $(TAR_FILE) into 30MB parts..."
	@rm -f maps6_part_*
	split -b 30m $(TAR_FILE) maps6_part_
	@ls -lh maps6_part_*

## clean: Remove build artifacts
clean:
	@echo "==> Cleaning build artifacts..."
	rm -f $(TAR_FILE) maps6_part_*
	@echo "==> Done."

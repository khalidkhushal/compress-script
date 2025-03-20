# Video Compression Tool

A web-based tool for compressing video files using FFmpeg with optimized settings.

## Features

- Drag and drop video upload
- Multiple file upload support
- Progress tracking
- Concurrent processing
- Automatic file cleanup
- Optimized compression settings

## Prerequisites

- Docker and Docker Compose
- At least 2GB RAM
- 10GB free disk space

## Quick Start

1. Clone the repository:
```bash
git clone <repository-url>
cd Video\ Compressing\ Script
```

2. Build and start the container:
```bash
docker-compose up --build
```
OR
```bash
docker compose up --build
```


3. Access the application:
   - Open your browser
   - Navigate to `http://localhost:8000`

## Docker Commands

- Start the application:
  ```bash
  docker-compose up
  ```

- Start in background:
  ```bash
  docker-compose up -d
  ```

- Stop the application:
  ```bash
  docker-compose down
  ```

- View logs:
  ```bash
  docker-compose logs -f
  ```

- Rebuild after changes:
  ```bash
  docker-compose up --build
  ```

## Troubleshooting

### Permission Issues

If you encounter permission issues with the uploads or output directories:

```bash
chmod -R 777 uploads/
chmod -R 777 output/
```

### FFmpeg Not Found

The Docker container includes FFmpeg by default. If you're running locally:

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

## Configuration

Default settings in `docker-compose.yml`:
```yaml
services:
  video-compressor:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./uploads:/app/uploads
      - ./output:/app/output
    environment:
      - PYTHONPATH=/app
```

## Compression Settings

The tool uses these FFmpeg parameters for optimal compression:
- Resolution: Up to 1280x720 (maintains aspect ratio)
- Video Codec: H.264
- Audio Codec: AAC
- CRF: 28 (balance between quality and size)
- Preset: medium
- Audio Bitrate: 128k

## License

MIT License

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

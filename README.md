# Background Removal Server

A high-performance REST API service for removing backgrounds from images using ONNX Runtime with GPU acceleration (CUDA). Built with FastAPI, optimized for NVIDIA A10/A100 GPUs.

## Features

- 🚀 **GPU Acceleration**: CUDA-powered inference with ONNX Runtime
- 🔐 **API Key Authentication**: Secure endpoint access with configurable API keys
- 📊 **Prometheus Metrics**: Built-in monitoring for requests, errors, and latency
- 🐳 **Docker Support**: Production-ready containerization with NVIDIA GPU support
- 🎯 **High Performance**: Optimized preprocessing and postprocessing pipeline
- 📝 **Structured Logging**: Request tracking with unique IDs and timing information
- ✅ **Health Checks**: Built-in health endpoint for service monitoring

## Technology Stack

- **Python 3.10+**
- **FastAPI**: Modern web framework for building APIs
- **ONNX Runtime GPU**: High-performance inference engine
- **OpenCV & NumPy**: Image processing
- **Uvicorn**: ASGI server
- **Prometheus Client**: Metrics collection
- **Docker & NVIDIA Container Toolkit**: Containerized deployment

## Project Structure

```
removebgServer/
├── app/
│   ├── __init__.py           # Package initialization
│   ├── main.py               # FastAPI application and routes
│   ├── infer.py              # Model loading and inference logic
│   ├── auth.py               # API key authentication
│   └── metrics.py            # Prometheus metrics
├── models/
│   ├── README.md             # Model download instructions
│   └── u2netp.onnx          # ONNX model file (download separately)
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker configuration for GPU
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

## Prerequisites

### For Local Development

- Python 3.10 or higher
- NVIDIA GPU with CUDA support (optional, will fall back to CPU)
- CUDA 11.8+ and cuDNN (for GPU acceleration)
- NVIDIA drivers (version 520+)

### For Docker Deployment

- Docker 20.10+
- NVIDIA Docker Runtime / NVIDIA Container Toolkit
- NVIDIA GPU with CUDA support

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/prettydt/removebgServer.git
cd removebgServer
```

### 2. Download the Model

Follow the instructions in `models/README.md` to download or convert the U2-Net ONNX model. Place the `u2netp.onnx` file in the `models/` directory.

Quick download (if you have a pre-converted model):
```bash
# Example - replace with actual model URL
wget -O models/u2netp.onnx [MODEL_URL]
```

### 3. Choose Installation Method

#### Option A: Local Python Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# For GPU support, ensure you have CUDA installed
# For CPU-only, replace onnxruntime-gpu with onnxruntime in requirements.txt
```

#### Option B: Docker Installation

```bash
# Build Docker image
docker build -t removebg-server .

# For custom model location during build
docker build -t removebg-server --build-arg MODEL_PATH=./models/u2netp.onnx .
```

## Configuration

### Environment Variables

- **`ALLOWED_KEYS`**: Comma-separated list of valid API keys (required for production)
  - Example: `ALLOWED_KEYS=key1,key2,key3`
  - If not set, authentication is disabled (development mode)

- **`MODEL_PATH`**: Path to ONNX model file (default: `models/u2netp.onnx`)

- **`HOST`**: Server host (default: `0.0.0.0`)

- **`PORT`**: Server port (default: `8000`)

### Example Configuration

Create a `.env` file (not tracked in git):

```bash
ALLOWED_KEYS=your-secret-key-1,your-secret-key-2
MODEL_PATH=models/u2netp.onnx
HOST=0.0.0.0
PORT=8000
```

## Running the Server

### Local Python

```bash
# Set environment variables
export ALLOWED_KEYS=test123,test456

# Run with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Or run directly
python -m app.main
```

### Docker (with GPU)

```bash
# Run with GPU support
docker run -d \
  --name removebg-server \
  --gpus all \
  -p 8000:8000 \
  -e ALLOWED_KEYS=test123,test456 \
  -v $(pwd)/models:/app/models \
  removebg-server

# Check logs
docker logs -f removebg-server
```

### Docker (CPU only)

For CPU-only deployment, modify `requirements.txt` to use `onnxruntime` instead of `onnxruntime-gpu`, then:

```bash
docker run -d \
  --name removebg-server \
  -p 8000:8000 \
  -e ALLOWED_KEYS=test123,test456 \
  -v $(pwd)/models:/app/models \
  removebg-server
```

### Docker Compose (Optional)

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  removebg:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ALLOWED_KEYS=test123,test456
      - MODEL_PATH=models/u2netp.onnx
    volumes:
      - ./models:/app/models
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

Run with:
```bash
docker-compose up -d
```

## API Usage

### Health Check

Check if the service is running and model is loaded:

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "model_loaded": true
}
```

### Remove Background

Remove background from an image:

```bash
curl -X POST http://localhost:8000/remove-bg \
  -H "x-api-key: test123" \
  -F "file=@/path/to/image.jpg" \
  --output result.png
```

#### Request

- **Method**: `POST`
- **Endpoint**: `/remove-bg`
- **Headers**:
  - `x-api-key`: Your API key (required)
- **Body**: `multipart/form-data`
  - `file`: Image file (jpg, png, or webp)
  - Maximum size: 10 MB

#### Response

- **Success (200)**: PNG image with transparent background
- **Headers**:
  - `Content-Type: image/png`
  - `X-Request-ID`: Unique request identifier
  - `X-Processing-Time`: Time taken to process (e.g., "2.45s")

#### Error Responses

- **400 Bad Request**: Invalid file format or empty file
- **401 Unauthorized**: Missing or invalid API key
- **413 Payload Too Large**: File exceeds 10 MB limit
- **500 Internal Server Error**: Processing failed
- **503 Service Unavailable**: Model not loaded

### Prometheus Metrics

Access Prometheus metrics for monitoring:

```bash
curl http://localhost:8000/metrics
```

Available metrics:
- `removebg_requests_total`: Total number of requests (by status)
- `removebg_errors_total`: Total number of errors (by error type)
- `removebg_request_duration_seconds`: Request latency histogram

## Example Scripts

### Python Client Example

```python
import requests

url = "http://localhost:8000/remove-bg"
headers = {"x-api-key": "test123"}

with open("input.jpg", "rb") as f:
    files = {"file": f}
    response = requests.post(url, headers=headers, files=files)

if response.status_code == 200:
    with open("output.png", "wb") as out:
        out.write(response.content)
    print("Background removed successfully!")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### Batch Processing Script

```bash
#!/bin/bash
API_KEY="test123"
INPUT_DIR="./input_images"
OUTPUT_DIR="./output_images"

mkdir -p "$OUTPUT_DIR"

for img in "$INPUT_DIR"/*.{jpg,png,jpeg}; do
    if [ -f "$img" ]; then
        filename=$(basename "$img")
        echo "Processing $filename..."
        curl -X POST http://localhost:8000/remove-bg \
          -H "x-api-key: $API_KEY" \
          -F "file=@$img" \
          --output "$OUTPUT_DIR/${filename%.*}.png"
    fi
done

echo "Batch processing complete!"
```

## Performance Optimization

### GPU Configuration

The service automatically uses CUDA if available. Check logs for:
```
Model loaded successfully using CUDAExecutionProvider
```

### Timeout Configuration

For large images or slow connections, configure timeouts:

**Uvicorn**:
```bash
uvicorn app.main:app --timeout-keep-alive 30
```

**Nginx Reverse Proxy**:
```nginx
location /remove-bg {
    proxy_pass http://localhost:8000;
    proxy_read_timeout 60s;
    proxy_connect_timeout 60s;
}
```

### Image Size Limits

The service limits images to 10 MB by default. To change:

Edit `app/main.py`:
```python
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
```

For very large images, the preprocessing automatically scales down to 512px on the longest edge while maintaining aspect ratio.

## Monitoring

### Structured Logs

All requests are logged with:
- Request ID (UUID)
- Client IP
- File size
- Processing time
- Status (success/error)

Example log:
```
2024-01-15 10:30:45 - app.main - INFO - [abc-123] Processing request from 192.168.1.100
2024-01-15 10:30:47 - app.main - INFO - [abc-123] Request completed successfully in 2.15s
```

### Prometheus Integration

Integrate with Prometheus for monitoring:

**prometheus.yml**:
```yaml
scrape_configs:
  - job_name: 'removebg'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboard

Create dashboards to visualize:
- Request rate and success rate
- Error distribution by type
- Latency percentiles (p50, p95, p99)
- GPU utilization (via NVIDIA DCGM exporter)

## Troubleshooting

### Model Not Loading

**Issue**: "Model file not found" error

**Solution**:
- Verify `models/u2netp.onnx` exists
- Check file permissions
- See `models/README.md` for download instructions

### GPU Not Detected

**Issue**: Service falls back to CPU

**Solution**:
- Check NVIDIA drivers: `nvidia-smi`
- Verify CUDA installation
- For Docker, ensure `--gpus all` flag is used
- Check logs for "CUDAExecutionProvider" message

### Out of Memory

**Issue**: CUDA out of memory errors

**Solution**:
- Reduce image size limit
- Lower the target_size in preprocessing (default 512)
- Use a smaller model variant

### Slow Performance

**Issue**: Processing takes too long

**Solution**:
- Verify GPU is being used (check logs)
- Reduce image size
- Check GPU utilization: `nvidia-smi`
- Consider batch processing for multiple images

## Production Deployment

### Security Recommendations

1. **Always set ALLOWED_KEYS** in production
2. Use HTTPS (configure reverse proxy like Nginx)
3. Implement rate limiting (e.g., with Nginx or Kong)
4. Monitor logs for suspicious activity
5. Regularly update dependencies

### Scaling

For high-traffic scenarios:

1. **Horizontal Scaling**: Deploy multiple instances behind a load balancer
2. **GPU Selection**: Use environment variable to select specific GPU
   ```bash
   CUDA_VISIBLE_DEVICES=0 uvicorn app.main:app
   ```
3. **Container Orchestration**: Use Kubernetes with GPU node pools

### Example Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: removebg-server
spec:
  replicas: 2
  selector:
    matchLabels:
      app: removebg
  template:
    metadata:
      labels:
        app: removebg
    spec:
      containers:
      - name: removebg
        image: removebg-server:latest
        ports:
        - containerPort: 8000
        env:
        - name: ALLOWED_KEYS
          valueFrom:
            secretKeyRef:
              name: removebg-secrets
              key: api-keys
        resources:
          limits:
            nvidia.com/gpu: 1
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio httpx

# Run tests (if test suite exists)
pytest tests/
```

### Code Quality

```bash
# Format code
black app/

# Lint code
flake8 app/
pylint app/

# Type checking
mypy app/
```

## License

[Add your license here]

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing issues for solutions

## Acknowledgments

- U2-Net model: [xuebinqin/U-2-Net](https://github.com/xuebinqin/U-2-Net)
- FastAPI framework
- ONNX Runtime team

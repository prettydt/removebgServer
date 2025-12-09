# Quick Start Guide

Get started with the Background Removal Server in 5 minutes!

## Prerequisites

- Docker with NVIDIA GPU support OR Python 3.10+
- NVIDIA GPU (optional, will use CPU if not available)

## Quick Start (Docker)

### 1. Clone and Navigate

```bash
git clone https://github.com/prettydt/removebgServer.git
cd removebgServer
```

### 2. Download Model

Follow instructions in `models/README.md` to get `u2netp.onnx` and place it in the `models/` directory.

### 3. Configure API Keys

```bash
cp .env.example .env
# Edit .env and set your API keys
```

### 4. Build and Run

```bash
# Build the Docker image
docker build -t removebg-server .

# Run with GPU support
docker run -d \
  --name removebg-server \
  --gpus all \
  -p 8000:8000 \
  -e ALLOWED_KEYS=test123 \
  -v $(pwd)/models:/app/models \
  removebg-server
```

Or use docker-compose:

```bash
docker-compose up -d
```

### 5. Test the Service

```bash
# Health check
curl http://localhost:8000/health

# Remove background (replace with your image)
curl -X POST http://localhost:8000/remove-bg \
  -H "x-api-key: test123" \
  -F "file=@test_image.jpg" \
  --output result.png
```

## Quick Start (Python)

### 1. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Download Model

Follow instructions in `models/README.md`.

### 3. Set Environment Variables

```bash
export ALLOWED_KEYS=test123
```

### 4. Run Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 5. Test

```bash
curl http://localhost:8000/health
```

## Common Issues

### Model Not Found

**Error**: "Model file not found: models/u2netp.onnx"

**Solution**: Download the model following `models/README.md` instructions.

### GPU Not Working

**Error**: Service uses CPU instead of GPU

**Solution**: 
- Ensure NVIDIA drivers are installed: `nvidia-smi`
- For Docker, use `--gpus all` flag
- Check logs for "CUDAExecutionProvider" message

### Port Already in Use

**Error**: Port 8000 already in use

**Solution**: 
- Stop other services on port 8000
- Or change port: `-e PORT=8080 -p 8080:8080`

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [API examples](#api-examples) below
- Configure monitoring with Prometheus

## API Examples

### Basic Request

```bash
curl -X POST http://localhost:8000/remove-bg \
  -H "x-api-key: test123" \
  -F "file=@image.jpg" \
  --output result.png
```

### With Progress

```bash
curl -X POST http://localhost:8000/remove-bg \
  -H "x-api-key: test123" \
  -F "file=@image.jpg" \
  -o result.png \
  --progress-bar
```

### Check Response Headers

```bash
curl -X POST http://localhost:8000/remove-bg \
  -H "x-api-key: test123" \
  -F "file=@image.jpg" \
  -D headers.txt \
  --output result.png

cat headers.txt
```

### Batch Processing

```bash
for img in *.jpg; do
  echo "Processing $img..."
  curl -X POST http://localhost:8000/remove-bg \
    -H "x-api-key: test123" \
    -F "file=@$img" \
    --output "${img%.jpg}_nobg.png"
done
```

## Python Client Example

```python
import requests

def remove_background(image_path, api_key="test123"):
    url = "http://localhost:8000/remove-bg"
    headers = {"x-api-key": api_key}
    
    with open(image_path, "rb") as f:
        files = {"file": f}
        response = requests.post(url, headers=headers, files=files)
    
    if response.status_code == 200:
        output_path = image_path.replace(".jpg", "_nobg.png")
        with open(output_path, "wb") as out:
            out.write(response.content)
        print(f"Saved to {output_path}")
        
        # Print processing time
        processing_time = response.headers.get('X-Processing-Time')
        print(f"Processing time: {processing_time}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

# Usage
remove_background("photo.jpg")
```

## Monitoring

### Check Metrics

```bash
curl http://localhost:8000/metrics
```

### Watch Logs (Docker)

```bash
docker logs -f removebg-server
```

### Check GPU Usage

```bash
watch -n 1 nvidia-smi
```

## Support

For more help:
- Check the [README.md](README.md)
- Review `models/README.md` for model setup
- Open an issue on GitHub

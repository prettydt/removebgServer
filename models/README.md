# Models Directory

This directory should contain the ONNX model file for background removal.

## Required Model

**File**: `u2netp.onnx`

## Download Instructions

You can obtain the U2-Net model in ONNX format through several methods:

### Option 1: Convert from PyTorch (Recommended)

1. Clone the U2-Net repository:
```bash
git clone https://github.com/xuebinqin/U-2-Net.git
cd U-2-Net
```

2. Download the pretrained U2-Net-P model:
```bash
# Download u2netp.pth (4.7 MB)
wget https://drive.google.com/uc?id=1rbSTGKAE-MTxBYHd-51l2hMOQPT_7EPy -O saved_models/u2netp/u2netp.pth
```

3. Convert to ONNX format using the provided conversion script:
```python
import torch
from model import U2NETP

# Load model
model = U2NETP(3, 1)
model.load_state_dict(torch.load('saved_models/u2netp/u2netp.pth', map_location='cpu'))
model.eval()

# Create dummy input
dummy_input = torch.randn(1, 3, 512, 512)

# Export to ONNX
torch.onnx.export(
    model,
    dummy_input,
    'u2netp.onnx',
    input_names=['input'],
    output_names=['output'],
    opset_version=11,
    dynamic_axes={
        'input': {0: 'batch_size', 2: 'height', 3: 'width'},
        'output': {0: 'batch_size', 2: 'height', 3: 'width'}
    }
)
```

4. Move the ONNX file to this directory:
```bash
mv u2netp.onnx /path/to/removebgServer/models/
```

### Option 2: Download Pre-converted ONNX Model

You can find pre-converted ONNX models from various sources:

- Check the ONNX Model Zoo
- Look for community conversions on GitHub
- Use online conversion services

### Option 3: Use Alternative Models

The service is designed to work with U2-Net-based models, but can be adapted for other segmentation models:

- MODNet
- BackgroundMattingV2
- RVM (Robust Video Matting)

Just ensure the model accepts RGB images and outputs a single-channel segmentation mask.

## Model Specifications

**U2-Net-P (Portable) Specifications:**
- Input: RGB image (3 channels)
- Input size: Dynamic (recommended 512x512 or smaller for speed)
- Output: Single-channel segmentation mask
- Model size: ~4.7 MB (PyTorch) / ~5 MB (ONNX)
- Architecture: Lightweight version of U2-Net

## Verification

After placing the model file, verify it works:

```bash
# Check if file exists
ls -lh models/u2netp.onnx

# Start the server and check health endpoint
curl http://localhost:8000/health
```

The health endpoint should show `"model_loaded": true` if the model was loaded successfully.

## Troubleshooting

**Issue**: Model file not found error

**Solution**: Ensure the file is named exactly `u2netp.onnx` and is placed in the `models/` directory.

**Issue**: ONNX Runtime fails to load model

**Solution**: 
- Verify the ONNX opset version is compatible (opset 11+ recommended)
- Check that the model was exported correctly
- Try re-converting the model with the correct opset version

**Issue**: GPU not being used

**Solution**:
- Ensure CUDA is properly installed
- Check that `onnxruntime-gpu` is installed (not `onnxruntime`)
- Verify NVIDIA drivers are up to date
- Check the application logs for the active provider (should show "CUDAExecutionProvider")

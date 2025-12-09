"""FastAPI main application entry point."""
import os
import sys
import uuid
import logging
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status, Request
from fastapi.responses import Response, StreamingResponse
import io

from app.auth import verify_api_key
from app.metrics import REQUEST_COUNT, ERROR_COUNT, get_metrics, timing_decorator
from app.infer import load_model, remove_background, check_model_loaded

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# File size limit (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Allowed image formats
ALLOWED_FORMATS = {'image/jpeg', 'image/png', 'image/webp'}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info("Starting up application...")
    try:
        model_path = os.getenv('MODEL_PATH', 'models/u2netp.onnx')
        load_model(model_path)
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Failed to load model during startup: {e}")
        logger.error("Application will start but /remove-bg endpoint will not work until model is loaded")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")


app = FastAPI(
    title="Background Removal API",
    description="REST API for removing backgrounds from images using ONNX Runtime with GPU support",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Dictionary with status information
    """
    model_loaded = check_model_loaded()
    return {
        "status": "ok",
        "model_loaded": model_loaded
    }


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    
    Returns:
        Prometheus metrics in text format
    """
    return get_metrics()


@app.post("/remove-bg")
@timing_decorator
async def remove_bg(
    request: Request,
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    """
    Remove background from uploaded image.
    
    Args:
        request: FastAPI request object
        file: Uploaded image file (jpg/png/webp)
        api_key: Validated API key from header
        
    Returns:
        PNG image with transparent background
        
    Raises:
        HTTPException: For various error conditions
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    logger.info(f"[{request_id}] Processing request from {request.client.host}")
    
    try:
        # Validate content type
        if file.content_type not in ALLOWED_FORMATS:
            ERROR_COUNT.labels(error_type='invalid_format').inc()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file format. Allowed formats: jpg, png, webp"
            )
        
        # Read file with size limit
        file_bytes = await file.read()
        file_size = len(file_bytes)
        
        logger.info(f"[{request_id}] Received file: {file.filename}, size: {file_size} bytes")
        
        if file_size > MAX_FILE_SIZE:
            ERROR_COUNT.labels(error_type='file_too_large').inc()
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
        
        if file_size == 0:
            ERROR_COUNT.labels(error_type='empty_file').inc()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file provided"
            )
        
        # Check if model is loaded
        if not check_model_loaded():
            ERROR_COUNT.labels(error_type='model_not_loaded').inc()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Model not loaded. Please check server logs."
            )
        
        # Process image
        try:
            result_bytes = remove_background(file_bytes)
        except ValueError as e:
            ERROR_COUNT.labels(error_type='processing_error').inc()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            ERROR_COUNT.labels(error_type='inference_error').inc()
            logger.error(f"[{request_id}] Inference error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process image"
            )
        
        # Calculate processing time
        duration = time.time() - start_time
        
        REQUEST_COUNT.labels(status='success').inc()
        logger.info(f"[{request_id}] Request completed successfully in {duration:.2f}s")
        
        # Return PNG image
        return Response(
            content=result_bytes,
            media_type="image/png",
            headers={
                "X-Request-ID": request_id,
                "X-Processing-Time": f"{duration:.2f}s"
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        REQUEST_COUNT.labels(status='error').inc()
        raise
    except Exception as e:
        # Catch any unexpected errors
        ERROR_COUNT.labels(error_type='unexpected').inc()
        logger.error(f"[{request_id}] Unexpected error: {e}", exc_info=True)
        REQUEST_COUNT.labels(status='error').inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        log_level="info"
    )

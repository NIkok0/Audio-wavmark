"""
WavMark Configuration

This module contains all configuration constants and parameters for the WavMark library.
"""

from typing import Dict, Any
import numpy as np
import torch

# Audio processing constants
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_N_FFT = 1000
DEFAULT_HOP_LENGTH = 400
DEFAULT_NUM_LAYERS = 8
DEFAULT_NUM_BIT = 32
DEFAULT_NUM_POINT = 16000

# Model configuration
DEFAULT_MODEL_CONFIG = {
    "num_point": DEFAULT_NUM_POINT,
    "num_bit": DEFAULT_NUM_BIT,
    "n_fft": DEFAULT_N_FFT,
    "hop_length": DEFAULT_HOP_LENGTH,
    "num_layers": DEFAULT_NUM_LAYERS
}

# Watermarking parameters
DEFAULT_PATTERN_BIT_LENGTH = 16
DEFAULT_MIN_SNR = 20.0
DEFAULT_MAX_SNR = 38.0
DEFAULT_SHIFT_RANGE = 0.1
DEFAULT_SHIFT_RANGE_P = 0.5

# Decoding parameters
DEFAULT_DECODE_BATCH_SIZE = 10
DEFAULT_MAX_ENCODE_ATTEMPTS = 10

# Quality metrics constants
EPSILON = 1e-10
DEFAULT_THRESHOLD = 0.5

# Pattern bits for watermark synchronization
# This pattern should be random but avoid all-zeros, all-ones, or periodic sequences
FIX_PATTERN = np.array([
    1, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0,
    0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1,
    1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1,
    1, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 1, 0,
    0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0
], dtype=np.int32)

# HuggingFace model configuration
HF_REPO_ID = "M4869/WavMark"
HF_MODEL_FILENAME = "step59000_snr39.99_pesq4.35_BERP_none0.30_mean1.81_std1.81.model.pkl"

# Logging configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
}

# Performance optimization settings
ENABLE_WINDOW_CACHING = True
ENABLE_BATCH_PROCESSING = True
DEFAULT_DEVICE = "auto"  # "auto", "cpu", "cuda"

# Validation settings
VALIDATE_INPUTS = True
VALIDATE_WATERMARK_LENGTH = True
VALIDATE_AUDIO_LENGTH = True

# Error handling settings
RETURN_ORIGINAL_ON_ERROR = True
LOG_ERRORS = True
RAISE_ON_CRITICAL_ERROR = False

# GPU Configuration
GPU_CONFIG = {
    "use_cuda": torch.cuda.is_available(),
    "device": "cuda" if torch.cuda.is_available() else "cpu",
    "num_workers": 4 if torch.cuda.is_available() else 0,
    "pin_memory": True if torch.cuda.is_available() else False,
    "batch_size": 32 if torch.cuda.is_available() else 8,
    "mixed_precision": True if torch.cuda.is_available() else False,
    "cudnn_benchmark": True if torch.cuda.is_available() else False,
}

# Set CUDA settings for better performance
if GPU_CONFIG["use_cuda"]:
    torch.backends.cudnn.benchmark = GPU_CONFIG["cudnn_benchmark"]
    if GPU_CONFIG["mixed_precision"]:
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

# Model Configuration
MODEL_CONFIG = {
    "num_point": 16000,
    "num_bit": 32,
    "n_fft": 1000,
    "hop_length": 400,
    "num_layers": 8
}

# Watermarking Configuration
WATERMARK_CONFIG = {
    "pattern_bit_length": 16,
    "min_snr": 20.0,
    "max_snr": 38.0,
    "target_snr": 30.0,
    "snr_tolerance": 2.0,
    "max_attempts": 5
}

# Decoding Configuration
DECODE_CONFIG = {
    "decode_batch_size": 16 if GPU_CONFIG["use_cuda"] else 8,
    "len_start_bit": 16,
    "confidence_threshold": 0.8
}

def get_gpu_config():
    """Get GPU configuration settings."""
    return GPU_CONFIG

def get_model_config():
    """Get model configuration settings."""
    return MODEL_CONFIG

def get_watermarking_config():
    """Get watermarking configuration settings."""
    return WATERMARK_CONFIG

def get_decoding_config():
    """Get decoding configuration settings."""
    return DECODE_CONFIG

def get_model_config(**kwargs) -> Dict[str, Any]:
    """
    Get model configuration with optional overrides.
    
    Args:
        **kwargs: Configuration overrides
        
    Returns:
        Model configuration dictionary
    """
    config = DEFAULT_MODEL_CONFIG.copy()
    config.update(kwargs)
    return config


def get_watermarking_config(**kwargs) -> Dict[str, Any]:
    """
    Get watermarking configuration with optional overrides.
    
    Args:
        **kwargs: Configuration overrides
        
    Returns:
        Watermarking configuration dictionary
    """
    config = {
        "pattern_bit_length": DEFAULT_PATTERN_BIT_LENGTH,
        "min_snr": DEFAULT_MIN_SNR,
        "max_snr": DEFAULT_MAX_SNR,
        "shift_range": DEFAULT_SHIFT_RANGE,
        "shift_range_p": DEFAULT_SHIFT_RANGE_P,
        "max_encode_attempts": DEFAULT_MAX_ENCODE_ATTEMPTS
    }
    config.update(kwargs)
    return config


def get_decoding_config(**kwargs) -> Dict[str, Any]:
    """
    Get decoding configuration with optional overrides.
    
    Args:
        **kwargs: Configuration overrides
        
    Returns:
        Decoding configuration dictionary
    """
    config = {
        "decode_batch_size": DEFAULT_DECODE_BATCH_SIZE,
        "shift_range_p": DEFAULT_SHIFT_RANGE_P
    }
    config.update(kwargs)
    return config


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration parameters.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Validate model config
        if "num_point" in config and config["num_point"] <= 0:
            return False
        if "num_bit" in config and config["num_bit"] <= 0:
            return False
        if "n_fft" in config and config["n_fft"] <= 0:
            return False
        if "hop_length" in config and config["hop_length"] <= 0:
            return False
        if "num_layers" in config and config["num_layers"] <= 0:
            return False
        
        # Validate watermarking config
        if "min_snr" in config and "max_snr" in config:
            if config["min_snr"] >= config["max_snr"]:
                return False
        
        if "pattern_bit_length" in config:
            if config["pattern_bit_length"] <= 0 or config["pattern_bit_length"] > len(FIX_PATTERN):
                return False
        
        # Validate decoding config
        if "decode_batch_size" in config and config["decode_batch_size"] <= 0:
            return False
        
        return True
        
    except Exception:
        return False 
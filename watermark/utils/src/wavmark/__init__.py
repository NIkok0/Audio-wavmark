"""
WavMark: Audio Watermarking Library

This module provides audio watermarking functionality using deep learning models.
Supports encoding and decoding watermarks in audio signals with configurable parameters.
"""

from typing import Optional, Tuple, Dict, Any, Union
import torch
import numpy as np
from huggingface_hub import hf_hub_download
import logging

from .utils import wm_add_util, file_reader, wm_decode_util, my_parser, metric_util, path_util
from .models import my_model

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_MODEL_CONFIG = {
    "num_point": 16000,
    "num_bit": 32,
    "n_fft": 1000,
    "hop_length": 400,
    "num_layers": 8
}

# Import advanced wrapper
try:
    from .advanced import WavMarkAdvanced
except ImportError as e:
    logger.warning(f"WavMarkAdvanced not available: {e}")
    WavMarkAdvanced = None


def load_model(path: str = "default", device: Optional[str] = None) -> my_model.Model:
    """
    Load the WavMark model from HuggingFace Hub or local path.
    
    Args:
        path: Model path. Use "default" for HuggingFace Hub model.
        device: Device to load model on ('cpu', 'cuda', etc.). If None, auto-detect.
    
    Returns:
        Loaded WavMark model in evaluation mode.
    
    Raises:
        RuntimeError: If model loading fails.
    """
    try:
        if path == "default":
            resume_path = hf_hub_download(
                repo_id="M4869/WavMark",
                filename="step59000_snr39.99_pesq4.35_BERP_none0.30_mean1.81_std1.81.model.pkl",
            )
        else:
            resume_path = path
        
        # Auto-detect device if not specified
        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        model = my_model.Model(**DEFAULT_MODEL_CONFIG)
        checkpoint = torch.load(resume_path, map_location=torch.device(device))
        model.load_state_dict(checkpoint, strict=True)
        model.to(device)
        model.eval()
        
        logger.info(f"Model loaded successfully on {device}")
        return model
        
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise RuntimeError(f"Model loading failed: {e}")


def encode_watermark(
    model: my_model.Model,
    signal: np.ndarray,
    payload: np.ndarray,
    pattern_bit_length: int = 16,
    min_snr: float = 20.0,
    max_snr: float = 38.0,
    show_progress: bool = False
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Encode watermark into audio signal.
    
    Args:
        model: Loaded WavMark model.
        signal: Input audio signal (numpy array).
        payload: Watermark payload bits (numpy array).
        pattern_bit_length: Length of pattern bits to use.
        min_snr: Minimum SNR threshold.
        max_snr: Maximum SNR threshold.
        show_progress: Whether to show progress bar.
    
    Returns:
        Tuple of (watermarked_signal, info_dict).
    
    Raises:
        ValueError: If payload length is invalid.
        AssertionError: If watermark length is not 32.
    """
    if len(payload) != 32 - pattern_bit_length:
        raise ValueError(f"Payload length must be {32 - pattern_bit_length}, got {len(payload)}")
    
    device = next(model.parameters()).device
    pattern_bit = wm_add_util.fix_pattern[:pattern_bit_length]
    watermark = np.concatenate([pattern_bit, payload])
    
    assert len(watermark) == 32, f"Watermark length must be 32, got {len(watermark)}"
    
    signal_wmd, info = wm_add_util.add_watermark(
        watermark, signal, DEFAULT_SAMPLE_RATE, 0.1,
        device, model, min_snr, max_snr, show_progress=show_progress
    )
    
    info["snr"] = metric_util.signal_noise_ratio(signal, signal_wmd)
    return signal_wmd, info


def decode_watermark(
    model: my_model.Model,
    signal: np.ndarray,
    decode_batch_size: int = 10,
    len_start_bit: int = 16,
    show_progress: bool = False,
    **kwargs
) -> Tuple[Optional[np.ndarray], Dict[str, Any]]:
    """
    Decode watermark from audio signal.
    
    Args:
        model: Loaded WavMark model.
        signal: Audio signal to decode from.
        decode_batch_size: Batch size for decoding.
        len_start_bit: Length of start bit pattern.
        show_progress: Whether to show progress bar.
        **kwargs: Additional keyword arguments for extract_watermark_v3_batch
    
    Returns:
        Tuple of (decoded_payload, info_dict). Returns (None, info) if no watermark found.
    """
    device = next(model.parameters()).device
    start_bit = wm_add_util.fix_pattern[:len_start_bit]
    
    mean_result, info = wm_decode_util.extract_watermark_v3_batch(
        signal, start_bit, 0.1, DEFAULT_SAMPLE_RATE, model, device,
        batch_size=decode_batch_size, show_progress=show_progress, **kwargs
    )
    
    if mean_result is None:
        return None, info
    
    payload = mean_result[len_start_bit:]
    return payload, info


# Backward compatibility aliases
__all__ = ['load_model', 'encode_watermark', 'decode_watermark', 'WavMarkAdvanced']

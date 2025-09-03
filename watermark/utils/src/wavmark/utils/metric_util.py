"""
Audio Quality Metrics Utilities

This module provides utilities for calculating audio quality metrics
such as SNR, BER, and other signal processing metrics.
"""

import torch
import numpy as np
from typing import Tuple, Union, Optional
import logging

logger = logging.getLogger(__name__)

# Constants
EPSILON = 1e-10
DEFAULT_THRESHOLD = 0.5


def calc_ber(
    watermark_decoded_tensor: torch.Tensor,
    watermark_tensor: torch.Tensor,
    threshold: float = DEFAULT_THRESHOLD
) -> torch.Tensor:
    """
    Calculate Bit Error Rate (BER) between decoded and original watermarks.
    
    Args:
        watermark_decoded_tensor: Decoded watermark tensor
        watermark_tensor: Original watermark tensor
        threshold: Threshold for binary conversion
        
    Returns:
        BER tensor (0 = perfect, 1 = completely wrong)
    """
    try:
        watermark_decoded_binary = watermark_decoded_tensor >= threshold
        watermark_binary = watermark_tensor >= threshold
        ber_tensor = 1 - (watermark_decoded_binary == watermark_binary).to(torch.float32).mean()
        return ber_tensor
        
    except Exception as e:
        logger.error(f"Error calculating BER: {e}")
        return torch.tensor(1.0)  # Return worst case BER


def to_equal_length(
    original: Union[np.ndarray, torch.Tensor],
    signal_watermarked: Union[np.ndarray, torch.Tensor]
) -> Tuple[Union[np.ndarray, torch.Tensor], Union[np.ndarray, torch.Tensor]]:
    """
    Ensure two signals have equal length by truncating to the shorter one.
    
    Args:
        original: Original signal
        signal_watermarked: Watermarked signal
        
    Returns:
        Tuple of (original_truncated, watermarked_truncated)
    """
    if original.shape != signal_watermarked.shape:
        logger.warning(f"Length mismatch: original={len(original)}, watermarked={len(signal_watermarked)}")
        min_length = min(len(original), len(signal_watermarked))
        original = original[:min_length]
        signal_watermarked = signal_watermarked[:min_length]
    
    assert original.shape == signal_watermarked.shape, f"Shape mismatch after truncation: {original.shape} vs {signal_watermarked.shape}"
    return original, signal_watermarked


def signal_noise_ratio(
    original: Union[np.ndarray, torch.Tensor],
    signal_watermarked: Union[np.ndarray, torch.Tensor]
) -> float:
    """
    Calculate Signal-to-Noise Ratio (SNR) between original and watermarked signals.
    
    Args:
        original: Original audio signal
        signal_watermarked: Watermarked audio signal
        
    Returns:
        SNR in dB (higher is better)
    """
    try:
        original, signal_watermarked = to_equal_length(original, signal_watermarked)
        
        # Convert to numpy if needed
        if isinstance(original, torch.Tensor):
            original = original.detach().cpu().numpy()
        if isinstance(signal_watermarked, torch.Tensor):
            signal_watermarked = signal_watermarked.detach().cpu().numpy()
        
        # Calculate noise
        noise = original - signal_watermarked
        
        # Calculate powers
        signal_power = np.sum(original ** 2)
        noise_power = np.sum(noise ** 2)
        
        # Handle edge cases
        if noise_power == 0:
            return np.inf  # Perfect reconstruction
        
        if signal_power == 0:
            return -np.inf  # No signal
        
        # Calculate SNR
        snr_linear = signal_power / max(noise_power, EPSILON)
        snr_db = 10 * np.log10(snr_linear)
        
        return float(snr_db)
        
    except Exception as e:
        logger.error(f"Error calculating SNR: {e}")
        return -np.inf


def batch_signal_noise_ratio(
    original: torch.Tensor,
    signal_watermarked: torch.Tensor
) -> float:
    """
    Calculate average SNR for a batch of signals.
    
    Args:
        original: Original signals tensor [batch, samples]
        signal_watermarked: Watermarked signals tensor [batch, samples]
        
    Returns:
        Average SNR in dB
    """
    try:
        original_np = original.detach().cpu().numpy()
        signal_watermarked_np = signal_watermarked.detach().cpu().numpy()
        
        snr_values = []
        for s, swm in zip(original_np, signal_watermarked_np):
            snr = signal_noise_ratio(s, swm)
            if np.isfinite(snr):
                snr_values.append(snr)
        
        if not snr_values:
            logger.warning("No valid SNR values found in batch")
            return -np.inf
        
        return float(np.mean(snr_values))
        
    except Exception as e:
        logger.error(f"Error calculating batch SNR: {e}")
        return -np.inf


def resample_to16k(
    data: np.ndarray,
    old_sr: int
) -> np.ndarray:
    """
    Resample audio data to 16kHz using simple decimation.
    
    Args:
        data: Input audio data
        old_sr: Original sample rate
        
    Returns:
        Resampled audio data at 16kHz
    """
    try:
        new_fs = 16000
        if old_sr == new_fs:
            return data
        
        # Simple decimation (for integer ratios)
        if old_sr % new_fs == 0:
            decimation_factor = old_sr // new_fs
            return data[::decimation_factor]
        else:
            # For non-integer ratios, use more sophisticated resampling
            logger.warning(f"Non-integer resampling ratio ({old_sr}/{new_fs}), using simple decimation")
            decimation_factor = int(old_sr / new_fs)
            return data[::decimation_factor]
            
    except Exception as e:
        logger.error(f"Error resampling audio: {e}")
        return data


def calculate_psnr(
    original: Union[np.ndarray, torch.Tensor],
    signal_watermarked: Union[np.ndarray, torch.Tensor]
) -> float:
    """
    Calculate Peak Signal-to-Noise Ratio (PSNR).
    
    Args:
        original: Original signal
        signal_watermarked: Watermarked signal
        
    Returns:
        PSNR in dB
    """
    try:
        original, signal_watermarked = to_equal_length(original, signal_watermarked)
        
        # Convert to numpy if needed
        if isinstance(original, torch.Tensor):
            original = original.detach().cpu().numpy()
        if isinstance(signal_watermarked, torch.Tensor):
            signal_watermarked = signal_watermarked.detach().cpu().numpy()
        
        # Calculate maximum possible signal value
        max_signal = np.max(np.abs(original))
        
        if max_signal == 0:
            return -np.inf
        
        # Calculate MSE
        mse = np.mean((original - signal_watermarked) ** 2)
        
        if mse == 0:
            return np.inf
        
        # Calculate PSNR
        psnr = 20 * np.log10(max_signal / np.sqrt(mse))
        return float(psnr)
        
    except Exception as e:
        logger.error(f"Error calculating PSNR: {e}")
        return -np.inf


def calculate_correlation(
    original: Union[np.ndarray, torch.Tensor],
    signal_watermarked: Union[np.ndarray, torch.Tensor]
) -> float:
    """
    Calculate correlation coefficient between original and watermarked signals.
    
    Args:
        original: Original signal
        signal_watermarked: Watermarked signal
        
    Returns:
        Correlation coefficient (-1 to 1, 1 = perfect correlation)
    """
    try:
        original, signal_watermarked = to_equal_length(original, signal_watermarked)
        
        # Convert to numpy if needed
        if isinstance(original, torch.Tensor):
            original = original.detach().cpu().numpy()
        if isinstance(signal_watermarked, torch.Tensor):
            signal_watermarked = signal_watermarked.detach().cpu().numpy()
        
        # Calculate correlation
        correlation = np.corrcoef(original.flatten(), signal_watermarked.flatten())[0, 1]
        
        return float(correlation) if not np.isnan(correlation) else 0.0
        
    except Exception as e:
        logger.error(f"Error calculating correlation: {e}")
        return 0.0

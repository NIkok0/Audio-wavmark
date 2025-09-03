"""
Watermark Addition Utilities

This module provides utilities for adding watermarks to audio signals.
"""

import torch
import numpy as np
from typing import Tuple, Dict, Any, Optional, Union
import tqdm
import time
import logging
from joblib import Parallel, delayed

from . import metric_util

logger = logging.getLogger(__name__)

# The pattern bits can be any random sequence.
# But don't use all-zeros, all-ones, or any periodic sequence, which will seriously hurt decoding performance.
fix_pattern = np.array([
    1, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0,
    0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1,
    1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1,
    1, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 1, 0,
    0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0
], dtype=np.int32)


def add_watermark(
    bit_arr: np.ndarray,
    data: np.ndarray,
    num_point: int,
    shift_range: float,
    device: torch.device,
    model: torch.nn.Module,
    min_snr: float,
    max_snr: float,
    show_progress: bool = False  # 生产环境默认关闭进度条
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Add watermark to audio data with SNR constraints.
    
    Args:
        bit_arr: Watermark bit array
        data: Input audio data
        num_point: Number of points per chunk
        shift_range: Shift range for overlapping
        device: Torch device
        model: WavMark model
        min_snr: Minimum SNR threshold
        max_snr: Maximum SNR threshold
        show_progress: Whether to show progress bar
        
    Returns:
        Tuple of (watermarked_data, info_dict)
    """
    start_time = time.time()
    chunk_size = num_point + int(num_point * shift_range)
    num_segments = len(data) // chunk_size
    len_remain = len(data) - num_segments * chunk_size
    if num_segments == 0:
        logger.warning("Audio too short for watermarking, returning original")
        return data, {"time_cost": 0, "encoded_sections": 0, "skip_sections": 0}
    # 批量切chunk
    chunks = np.lib.stride_tricks.as_strided(
        data[:num_segments*chunk_size],
        shape=(num_segments, chunk_size),
        strides=(data.strides[0]*chunk_size, data.strides[0])
    ).copy()
    cover_chunks = chunks[:, :num_point]
    shift_chunks = chunks[:, num_point:]
    # 批量encode
    encoded_cover_chunks = encode_chunk_batch(cover_chunks, bit_arr, device, model)
    # 批量SNR
    snrs = Parallel(n_jobs=-1)(delayed(metric_util.signal_noise_ratio)(cover_chunks[i], encoded_cover_chunks[i]) for i in range(len(cover_chunks)))
    snrs = np.array(snrs)
    # 合格的直接用，不合格的单独retry
    mask_ok = (snrs >= min_snr) & (snrs <= max_snr)
    final_cover_chunks = encoded_cover_chunks.copy()
    retry_indices = np.where(~mask_ok)[0]
    for idx in retry_indices:
        chunk, _ = encode_chunk_with_snr_check(idx, cover_chunks[idx], bit_arr, device, model, min_snr, max_snr)
        final_cover_chunks[idx] = chunk
    # 拼回完整chunk
    output_chunks = [np.concatenate([final_cover_chunks[i], shift_chunks[i]]) for i in range(num_segments)]
    if len_remain > 0:
        output_chunks.append(data[-len_remain:])
    reconstructed_array = np.concatenate(output_chunks)
    time_cost = time.time() - start_time
    info = {
        "time_cost": time_cost,
        "encoded_sections": int(mask_ok.sum()),
        "skip_sections": int((snrs < min_snr).sum()),
        "total_sections": num_segments,
        "success_rate": int(mask_ok.sum()) / max(num_segments, 1)
    }
    # 仅建议 debug 时开启 show_progress
    # if show_progress:
    #     iterator = tqdm.tqdm(iterator, desc="Adding watermark")
    logger.info(f"Watermarking completed: {int(mask_ok.sum())}/{num_segments} sections encoded "
                f"({info['success_rate']:.1%} success rate) in {time_cost:.2f}s")
    return reconstructed_array, info


def encode_chunk_with_snr_check(
    idx_chunk: int,
    signal: np.ndarray,
    wm: np.ndarray,
    device: torch.device,
    model: torch.nn.Module,
    min_snr: float,
    max_snr: float
) -> Tuple[np.ndarray, Union[str, int]]:
    """
    Encode a chunk with SNR constraint checking.
    
    Args:
        idx_chunk: Chunk index
        signal: Input signal chunk
        wm: Watermark bits
        device: Torch device
        model: WavMark model
        min_snr: Minimum SNR threshold
        max_snr: Maximum SNR threshold
        
    Returns:
        Tuple of (encoded_signal, state_or_attempts)
    """
    signal_for_encode = signal.copy()
    encode_times = 0
    max_attempts = 10
    
    while encode_times < max_attempts:
        encode_times += 1
        signal_wmd = encode_chunk(signal_for_encode, wm, device, model)
        snr = metric_util.signal_noise_ratio(signal, signal_wmd)
        
        # Check if SNR is too low on first attempt
        if encode_times == 1 and snr < min_snr:
            logger.debug(f"Skip section {idx_chunk}: SNR too low ({snr:.1f} < {min_snr})")
            return signal, "skip"
        
        # Check if SNR is within acceptable range
        if snr <= max_snr:
            return signal_wmd, encode_times
        
        # SNR is too high, use current result as input for next iteration
        signal_for_encode = signal_wmd
    
    # Max attempts reached
    logger.debug(f"Section {idx_chunk}: Max attempts ({max_attempts}) reached, final SNR: {snr:.1f}")
    return signal_wmd, encode_times


def encode_chunk(
    chunk: np.ndarray,
    wm: np.ndarray,
    device: torch.device,
    model: torch.nn.Module
) -> np.ndarray:
    """
    Encode a single chunk with watermark.
    
    Args:
        chunk: Input audio chunk
        wm: Watermark bits
        device: Torch device
        model: WavMark model
        
    Returns:
        Encoded audio chunk
    """
    with torch.no_grad():
        try:
            signal = torch.from_numpy(chunk).float().to(device).unsqueeze(0)
            message = torch.from_numpy(wm).float().to(device).unsqueeze(0)
            signal_wmd_tensor = model.encode(signal, message)
            signal_wmd = signal_wmd_tensor.detach().cpu().numpy().squeeze()
            return signal_wmd
        except Exception as e:
            logger.error(f"Error encoding chunk: {e}")
            return chunk


def encode_chunk_batch(
    chunks: np.ndarray,
    wm: np.ndarray,
    device: torch.device,
    model: torch.nn.Module
) -> np.ndarray:
    """
    批量编码 chunk，chunks: [B, N]，wm: [B, K] or [K]
    """
    with torch.no_grad():
        try:
            signal = torch.from_numpy(chunks).float().to(device)
            if wm.ndim == 1:
                message = torch.from_numpy(wm).float().to(device).unsqueeze(0).repeat(len(chunks), 1)
            else:
                message = torch.from_numpy(wm).float().to(device)
            signal_wmd_tensor = model.encode(signal, message)
            signal_wmd = signal_wmd_tensor.detach().cpu().numpy()
            return signal_wmd
        except Exception as e:
            logger.error(f"Error batch encoding: {e}")
            return chunks


def validate_watermark_bits(bit_arr: np.ndarray, expected_length: int = 32) -> bool:
    """
    Validate watermark bit array.
    
    Args:
        bit_arr: Bit array to validate
        expected_length: Expected length of bit array
        
    Returns:
        True if valid, False otherwise
    """
    if len(bit_arr) != expected_length:
        logger.error(f"Invalid watermark length: {len(bit_arr)}, expected {expected_length}")
        return False
    
    if not np.all(np.isin(bit_arr, [0, 1])):
        logger.error("Watermark contains non-binary values")
        return False
    
    return True

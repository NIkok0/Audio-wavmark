"""
Watermark Decoding Utilities

This module provides utilities for decoding watermarks from audio signals.
"""

# import pdb

import torch
import numpy as np
from typing import Tuple, Dict, Any, Optional, List
import tqdm
import time
import logging
from joblib import Parallel, delayed

logger = logging.getLogger(__name__)


def decode_chunk(
    chunk: np.ndarray,
    model: torch.nn.Module,
    device: torch.device
) -> np.ndarray:
    """
    Decode watermark from a single chunk.
    
    Args:
        chunk: Input audio chunk
        model: WavMark model
        device: Torch device
        
    Returns:
        Decoded bit array
    """
    with torch.no_grad():
        try:
            signal = torch.FloatTensor(chunk).to(device).unsqueeze(0)
            message = (model.decode(signal) >= 0.5).int()
            message = message.detach().cpu().numpy().squeeze()
            return message
            
        except Exception as e:
            logger.error(f"Error decoding chunk: {e}")
            # Return zeros on error
            return np.zeros(32, dtype=np.int32)


def extract_watermark_v3_batch(
    data: np.ndarray,
    start_bit: np.ndarray,
    shift_range: float,
    num_point: int,
    model: torch.nn.Module,
    device: torch.device,
    batch_size: int = 32,
    shift_range_p: float = 0.5,
    show_progress: bool = False  # 生产环境默认关闭进度条
) -> Tuple[Optional[np.ndarray], Dict[str, Any]]:
    """
    Extract watermark using batch processing with sliding window.
    
    Args:
        data: Input audio data
        start_bit: Start bit pattern to match
        shift_range: Shift range for detection
        num_point: Number of points per detection window
        model: WavMark model
        device: Torch device
        batch_size: Batch size for processing
        shift_range_p: Shift range percentage
        show_progress: Whether to show progress bar
        
    Returns:
        Tuple of (decoded_watermark, info_dict)
    """
    start_time = time.time()
    
    # Calculate detection parameters
    shift_step = int(shift_range * num_point * shift_range_p)
    total_detections = (len(data) - num_point) // shift_step
    
    if total_detections <= 0:
        logger.warning("Audio too short for watermark detection")
        return None, {"time_cost": 0, "results": []}
    
    total_detect_points = [i * shift_step for i in range(total_detections)]
    total_batch_counts = (len(total_detect_points) + batch_size - 1) // batch_size
    
    results = []
    
    # Process batches
    iterator = range(total_batch_counts)
    # 仅建议 debug 时开启 show_progress
    # if show_progress:
    #     iterator = tqdm.tqdm(iterator, desc="Decoding watermark")
    
    for i in iterator:
        start_idx = i * batch_size
        end_idx = min(start_idx + batch_size, len(total_detect_points))
        detect_points = total_detect_points[start_idx:end_idx]
        
        if not detect_points:
            break
        
        # Prepare batch
        arr = np.lib.stride_tricks.as_strided(
            data,
            shape=(len(detect_points), num_point),
            strides=(data.strides[0]*shift_step, data.strides[0])
        )
        current_batch = arr.copy()  # 保证内存连续
        
        # Process batch
        batch_results = process_decode_batch(
            current_batch, detect_points, start_bit, model, device
        )
        results.extend(batch_results)
    
    end_time = time.time()
    time_cost = end_time - start_time
    
    info = {
        "time_cost": time_cost,
        "results": results,
        "total_detections": total_detections,
        "successful_detections": len(results)
    }
    
    if not results:
        logger.info("No watermark detected")
        return None, info
    
    # Calculate final result
    results_perfect = [r["msg"] for r in results if np.isclose(r["sim"], 1.0)]
    
    if not results_perfect:
        logger.warning("No perfect matches found, using best matches")
        # Use all results if no perfect matches
        results_perfect = [r["msg"] for r in results]
    
    mean_result = (np.array(results_perfect).mean(axis=0) >= 0.5).astype(int)
    
    logger.info(f"Watermark detection completed: {len(results)}/{total_detections} successful "
                f"detections in {time_cost:.2f}s")
    
    return mean_result, info


def process_decode_batch(
    batch: np.ndarray,
    detect_points: List[int],
    start_bit: np.ndarray,
    model: torch.nn.Module,
    device: torch.device
) -> List[Dict[str, Any]]:
    """
    Process a batch of audio chunks for watermark detection.
    
    Args:
        batch: Batch of audio chunks
        detect_points: Detection point indices
        start_bit: Start bit pattern
        model: WavMark model
        device: Torch device
        
    Returns:
        List of detection results
    """
    results = []
    
    with torch.no_grad():
        try:
            # 优化5/6：混合精度+减少拷贝
            with torch.amp.autocast('cuda', enabled=(device.type=="cuda")):
                signal = torch.from_numpy(batch).float().to(device)
                batch_message = (model.decode(signal) >= 0.5).int().detach().cpu().numpy()
            # 优化3/6：并行 analyze_detection_result
            results = Parallel(n_jobs=-1)(
                delayed(analyze_detection_result)(p, bit_array, start_bit)
                for p, bit_array in zip(detect_points, batch_message)
            )
            results = [r for r in results if r is not None]
        except Exception as e:
            logger.error(f"Error processing decode batch: {e}")
    
    return results


def analyze_detection_result(
    position: int,
    bit_array: np.ndarray,
    start_bit: np.ndarray
) -> Optional[Dict[str, Any]]:
    """
    Analyze a single detection result.
    
    Args:
        position: Detection position
        bit_array: Decoded bit array
        start_bit: Expected start bit pattern
        
    Returns:
        Detection result dict or None if no match
    """
    decoded_start_bit = bit_array[:len(start_bit)]
    ber_start_bit = 1 - np.mean(start_bit == decoded_start_bit)
    num_equal_bits = np.sum(start_bit == decoded_start_bit)
    
    # Only accept exact matches for start bits
    if ber_start_bit > 0:
        return None
    
    return {
        "sim": 1 - ber_start_bit,
        "num_equal_bits": num_equal_bits,
        "msg": bit_array,
        "start_position": position,
        "start_time_position": position / 16000
    }


def validate_start_bit_pattern(start_bit: np.ndarray) -> bool:
    """
    Validate start bit pattern.
    
    Args:
        start_bit: Start bit pattern to validate
        
    Returns:
        True if valid, False otherwise
    """
    if len(start_bit) == 0:
        logger.error("Start bit pattern is empty")
        return False
    
    if not np.all(np.isin(start_bit, [0, 1])):
        logger.error("Start bit pattern contains non-binary values")
        return False
    
    return True


def calculate_detection_confidence(results: List[Dict[str, Any]]) -> float:
    """
    Calculate confidence score for detection results.
    
    Args:
        results: List of detection results
        
    Returns:
        Confidence score between 0 and 1
    """
    if not results:
        return 0.0
    
    # Calculate average similarity
    avg_sim = np.mean([r["sim"] for r in results])
    
    # Consider number of detections
    num_detections = len(results)
    detection_factor = min(num_detections / 10.0, 1.0)  # Normalize to max 10 detections
    
    return avg_sim * detection_factor

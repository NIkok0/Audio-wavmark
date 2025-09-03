"""
Basic Usage Example for WavMark

This example demonstrates how to use the optimized WavMark library
for audio watermarking and decoding.
"""

import numpy as np
import torch
import logging
from pathlib import Path

# Import WavMark
from wavmark import load_model, encode_watermark, decode_watermark
from wavmark.config import get_watermarking_config, get_decoding_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_audio(duration_seconds: float = 5.0, sample_rate: int = 16000) -> np.ndarray:
    """
    Create a test audio signal for demonstration.
    
    Args:
        duration_seconds: Duration of the audio in seconds
        sample_rate: Sample rate in Hz
        
    Returns:
        Test audio signal
    """
    num_samples = int(duration_seconds * sample_rate)
    
    # Create a simple sine wave with some noise
    t = np.linspace(0, duration_seconds, num_samples)
    frequency = 440  # A4 note
    signal = 0.5 * np.sin(2 * np.pi * frequency * t)
    
    # Add some noise
    noise = 0.01 * np.random.randn(num_samples)
    signal += noise
    
    return signal


def create_test_payload(payload_length: int = 16) -> np.ndarray:
    """
    Create a test watermark payload.
    
    Args:
        payload_length: Length of the payload in bits
        
    Returns:
        Binary payload array
    """
    return np.random.randint(0, 2, payload_length, dtype=np.int32)


def main():
    """Main demonstration function."""
    logger.info("Starting WavMark demonstration...")
    
    # Create test data
    logger.info("Creating test audio and payload...")
    audio_signal = create_test_audio(duration_seconds=3.0)
    payload = create_test_payload(payload_length=16)
    
    logger.info(f"Audio signal shape: {audio_signal.shape}")
    logger.info(f"Payload: {payload}")
    
    # Load model
    logger.info("Loading WavMark model...")
    try:
        model = load_model(device="auto")  # Auto-detect device
        logger.info(f"Model loaded successfully on {next(model.parameters()).device}")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return
    
    # Get configurations
    wm_config = get_watermarking_config(
        min_snr=25.0,  # Higher quality requirement
        max_snr=35.0   # Lower distortion
    )
    
    decode_config = get_decoding_config(
        decode_batch_size=20  # Larger batch for faster processing
    )
    
    # Encode watermark
    logger.info("Encoding watermark...")
    try:
        watermarked_audio, encode_info = encode_watermark(
            model=model,
            signal=audio_signal,
            payload=payload,
            pattern_bit_length=wm_config["pattern_bit_length"],
            min_snr=wm_config["min_snr"],
            max_snr=wm_config["max_snr"],
            show_progress=True
        )
        
        logger.info(f"Encoding completed:")
        logger.info(f"  - Time cost: {encode_info['time_cost']:.2f}s")
        logger.info(f"  - Encoded sections: {encode_info['encoded_sections']}")
        logger.info(f"  - Skip sections: {encode_info['skip_sections']}")
        logger.info(f"  - Success rate: {encode_info['success_rate']:.1%}")
        logger.info(f"  - Final SNR: {encode_info['snr']:.1f} dB")
        
    except Exception as e:
        logger.error(f"Encoding failed: {e}")
        return
    
    # Decode watermark
    logger.info("Decoding watermark...")
    try:
        decoded_payload, decode_info = decode_watermark(
            model=model,
            signal=watermarked_audio,
            decode_batch_size=decode_config["decode_batch_size"],
            len_start_bit=wm_config["pattern_bit_length"],
            show_progress=True
        )
        
        logger.info(f"Decoding completed:")
        logger.info(f"  - Time cost: {decode_info['time_cost']:.2f}s")
        logger.info(f"  - Total detections: {decode_info['total_detections']}")
        logger.info(f"  - Successful detections: {decode_info['successful_detections']}")
        
        if decoded_payload is not None:
            logger.info(f"  - Decoded payload: {decoded_payload}")
            
            # Calculate bit error rate
            ber = np.mean(payload != decoded_payload)
            logger.info(f"  - Bit Error Rate: {ber:.3f} ({ber*100:.1f}%)")
            
            if ber == 0:
                logger.info("✅ Perfect decoding achieved!")
            elif ber < 0.1:
                logger.info("✅ Good decoding quality")
            else:
                logger.warning("⚠️  High bit error rate detected")
        else:
            logger.error("❌ No watermark detected")
            
    except Exception as e:
        logger.error(f"Decoding failed: {e}")
        return
    
    # Save results
    logger.info("Saving results...")
    try:
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Save audio files
        np.save(output_dir / "original_audio.npy", audio_signal)
        np.save(output_dir / "watermarked_audio.npy", watermarked_audio)
        np.save(output_dir / "original_payload.npy", payload)
        
        if decoded_payload is not None:
            np.save(output_dir / "decoded_payload.npy", decoded_payload)
        
        logger.info(f"Results saved to {output_dir}")
        
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
    
    logger.info("Demonstration completed!")


def benchmark_performance():
    """Benchmark the performance of different configurations."""
    logger.info("Starting performance benchmark...")
    
    # Load model
    model = load_model(device="auto")
    
    # Test different audio lengths
    audio_lengths = [1.0, 3.0, 5.0, 10.0]  # seconds
    payload = create_test_payload(16)
    
    results = []
    
    for duration in audio_lengths:
        logger.info(f"Testing with {duration}s audio...")
        
        audio = create_test_audio(duration)
        
        # Time encoding
        start_time = torch.cuda.Event(enable_timing=True) if torch.cuda.is_available() else None
        end_time = torch.cuda.Event(enable_timing=True) if torch.cuda.is_available() else None
        
        if start_time:
            start_time.record()
        
        watermarked, encode_info = encode_watermark(
            model, audio, payload, show_progress=False
        )
        
        if end_time:
            end_time.record()
            torch.cuda.synchronize()
            encode_time = start_time.elapsed_time(end_time) / 1000.0
        else:
            encode_time = encode_info['time_cost']
        
        # Time decoding
        if start_time:
            start_time.record()
        
        decoded, decode_info = decode_watermark(
            model, watermarked, show_progress=False
        )
        
        if end_time:
            end_time.record()
            torch.cuda.synchronize()
            decode_time = start_time.elapsed_time(end_time) / 1000.0
        else:
            decode_time = decode_info['time_cost']
        
        # Calculate metrics
        ber = np.mean(payload != decoded) if decoded is not None else 1.0
        
        results.append({
            'duration': duration,
            'encode_time': encode_time,
            'decode_time': decode_time,
            'total_time': encode_time + decode_time,
            'snr': encode_info['snr'],
            'ber': ber,
            'success_rate': encode_info['success_rate']
        })
        
        logger.info(f"  - Encode: {encode_time:.2f}s, Decode: {decode_time:.2f}s")
        logger.info(f"  - SNR: {encode_info['snr']:.1f}dB, BER: {ber:.3f}")
    
    # Print summary
    logger.info("\nPerformance Summary:")
    logger.info("Duration | Encode(s) | Decode(s) | Total(s) | SNR(dB) | BER")
    logger.info("-" * 60)
    
    for result in results:
        logger.info(f"{result['duration']:8.1f} | {result['encode_time']:9.2f} | "
                   f"{result['decode_time']:8.2f} | {result['total_time']:7.2f} | "
                   f"{result['snr']:7.1f} | {result['ber']:.3f}")


if __name__ == "__main__":
    # Run basic demonstration
    main()
    
    # Run performance benchmark
    print("\n" + "="*60)
    benchmark_performance() 
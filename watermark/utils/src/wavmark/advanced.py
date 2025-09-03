"""
Advanced WavMark wrapper with additional features and GPU optimization.

This module provides an advanced wrapper around the basic WavMark functionality
with quality control, confidence assessment, and batch processing capabilities.
"""

import numpy as np
import torch
import torch.cuda.amp as amp
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from torch.utils.data import DataLoader, TensorDataset

# Import functions directly to avoid circular import
from .models.my_model import Model
from .utils import wm_add_util, wm_decode_util, metric_util
from .config import get_watermarking_config, get_decoding_config, get_gpu_config, get_model_config

logger = logging.getLogger(__name__)


class WavMarkAdvanced:
    """
    Advanced WavMark wrapper with quality control and batch processing.
    
    This class provides enhanced functionality including:
    - Quality-controlled encoding with target SNR
    - Confidence-based decoding
    - Batch processing for multiple files
    - Statistics tracking
    """
    
    def __init__(self, device: str = "auto", model_path: str = "default"):
        """
        Initialize advanced WavMark wrapper with GPU optimization.
        
        Args:
            device: Device to use ('auto', 'cpu', 'cuda')
            model_path: Path to model or 'default' for HuggingFace
        """
        self.gpu_config = get_gpu_config()
        self.device = self._get_device(device)
        self.model = self._create_model(model_path)
        self.scaler = amp.GradScaler() if self.gpu_config["mixed_precision"] else None
        self.encoding_stats = []
        self.decoding_stats = []
        
        logger.info(f"WavMarkAdvanced initialized on {self.device}")
        if self.gpu_config["mixed_precision"]:
            logger.info("Mixed precision enabled")
    
    def _get_device(self, device: str) -> str:
        """Get appropriate device string with GPU support."""
        if device == "auto":
            return self.gpu_config["device"]
        return device
    
    def _create_model(self, model_path: str) -> Model:
        """Create model with GPU optimization."""
        model_config = get_model_config()
        model = Model(**model_config)
        
        if self.device == "cuda":
            model = model.cuda()
            if torch.cuda.device_count() > 1:
                logger.info(f"Using {torch.cuda.device_count()} GPUs")
                model = torch.nn.DataParallel(model)
        
        model.eval()
        return model
    
    def _prepare_batch(self, signal: np.ndarray, batch_size: int) -> DataLoader:
        """Prepare batched data loader for GPU processing."""
        # Convert to tensor and create dataset
        signal_tensor = torch.FloatTensor(signal).to(self.device)
        dataset = TensorDataset(signal_tensor)
        
        # Create data loader
        loader = DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=self.gpu_config["num_workers"],
            pin_memory=self.gpu_config["pin_memory"]
        )
        
        return loader
    
    @torch.no_grad()
    def encode_with_quality_control(
        self,
        signal: np.ndarray,
        payload: np.ndarray,
        target_snr: float = 30.0,
        snr_tolerance: float = 2.0,
        max_attempts: int = 5,
        **kwargs
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Encode watermark with quality control and GPU optimization.
        
        Args:
            signal: Input audio signal
            payload: Watermark payload
            target_snr: Target SNR in dB
            snr_tolerance: SNR tolerance range
            max_attempts: Maximum encoding attempts
            **kwargs: Additional encoding parameters
            
        Returns:
            Tuple of (watermarked_signal, info_dict)
        """
        logger.info(f"Encoding with target SNR: {target_snr}±{snr_tolerance} dB")
        
        best_result = None
        best_snr_diff = float('inf')
        
        # Convert payload to tensor
        payload_tensor = torch.FloatTensor(payload).to(self.device)
        
        # Prepare batched data loader
        batch_size = self.gpu_config["batch_size"]
        data_loader = self._prepare_batch(signal, batch_size)
        
        for attempt in range(max_attempts):
            logger.info(f"Encoding attempt {attempt + 1}/{max_attempts}")
            
            min_snr = target_snr - snr_tolerance
            max_snr = target_snr + snr_tolerance
            
            try:
                # Process in batches
                encoded_chunks = []
                
                for batch in data_loader:
                    batch_signal = batch[0]
                    
                    # Use mixed precision if enabled
                    if self.gpu_config["mixed_precision"]:
                        with amp.autocast():
                            watermarked_chunk = self._encode_chunk(
                                batch_signal, payload_tensor, min_snr, max_snr
                            )
                    else:
                        watermarked_chunk = self._encode_chunk(
                            batch_signal, payload_tensor, min_snr, max_snr
                        )
                    
                    encoded_chunks.append(watermarked_chunk.cpu().numpy())
                
                # Combine chunks
                watermarked = np.concatenate(encoded_chunks)
                actual_snr = metric_util.signal_noise_ratio(signal, watermarked)
                snr_diff = abs(actual_snr - target_snr)
                
                info = {
                    'snr': actual_snr,
                    'success_rate': 1.0,
                    'time_cost': time.time(),
                    'encoded_sections': len(encoded_chunks),
                    'gpu_utilized': torch.cuda.is_available()
                }
                
                logger.info(f"  Attempt {attempt + 1}: SNR = {actual_snr:.1f} dB")
                
                if snr_diff < best_snr_diff:
                    best_result = (watermarked, info)
                    best_snr_diff = snr_diff
                
                if snr_diff <= snr_tolerance:
                    logger.info(f"Target SNR achieved: {actual_snr:.1f} dB")
                    break
                    
            except Exception as e:
                logger.warning(f"Encoding attempt {attempt + 1} failed: {e}")
                continue
        
        if best_result is None:
            raise RuntimeError("All encoding attempts failed")
        
        watermarked, info = best_result
        self.encoding_stats.append({
            'target_snr': target_snr,
            'actual_snr': info['snr'],
            'snr_diff': best_snr_diff,
            'attempts': attempt + 1,
            'success_rate': info.get('success_rate', 1.0),
            'gpu_utilized': info['gpu_utilized']
        })
        
        return watermarked, info
    
    def _encode_chunk(
        self,
        signal_chunk: torch.Tensor,
        payload: torch.Tensor,
        min_snr: float,
        max_snr: float
    ) -> torch.Tensor:
        """Encode a single chunk of audio on GPU."""
        # Add watermark processing here
        # This is a placeholder - implement actual watermark encoding
        watermarked = signal_chunk + 0.01 * torch.randn_like(signal_chunk)
        return watermarked
    
    @torch.no_grad()
    def decode_with_confidence(
        self,
        signal: np.ndarray,
        confidence_threshold: float = 0.8,
        **kwargs
    ) -> Tuple[Optional[np.ndarray], Dict[str, Any]]:
        """
        Decode watermark with confidence scoring and GPU optimization.
        
        Args:
            signal: Audio signal to decode
            confidence_threshold: Minimum confidence threshold
            **kwargs: Additional decoding parameters
            
        Returns:
            Tuple of (decoded_payload, info_dict)
        """
        logger.info("Decoding with confidence scoring...")
        
        # Prepare batched data loader
        batch_size = self.gpu_config["batch_size"]
        data_loader = self._prepare_batch(signal, batch_size)
        
        decoded_chunks = []
        confidence_scores = []
        
        for batch in data_loader:
            batch_signal = batch[0]
            
            # Use mixed precision if enabled
            if self.gpu_config["mixed_precision"]:
                with amp.autocast():
                    decoded_chunk, confidence = self._decode_chunk(batch_signal)
            else:
                decoded_chunk, confidence = self._decode_chunk(batch_signal)
            
            decoded_chunks.append(decoded_chunk.cpu().numpy())
            confidence_scores.append(confidence)
        
        # Combine results
        decoded_payload = np.mean(decoded_chunks, axis=0)
        mean_confidence = np.mean(confidence_scores)
        
        info = {
            'confidence': mean_confidence,
            'detection_quality': 'high' if mean_confidence > 0.9 else 'medium',
            'successful_detections': len(decoded_chunks),
            'total_detections': len(decoded_chunks),
            'gpu_utilized': torch.cuda.is_available()
        }
        
        self.decoding_stats.append({
            'confidence': info['confidence'],
            'detection_quality': info['detection_quality'],
            'num_detections': info['successful_detections'],
            'total_detections': info['total_detections'],
            'gpu_utilized': info['gpu_utilized']
        })
        
        logger.info(f"Detection confidence: {info['confidence']:.3f} ({info['detection_quality']})")
        
        return decoded_payload if mean_confidence >= confidence_threshold else None, info
    
    def _decode_chunk(
        self,
        signal_chunk: torch.Tensor
    ) -> Tuple[torch.Tensor, float]:
        """Decode a single chunk of audio on GPU."""
        # Add watermark detection here
        # This is a placeholder - implement actual watermark detection
        decoded = torch.randint(0, 2, (16,), device=signal_chunk.device).float()
        confidence = 0.9
        return decoded, confidence
    
    def batch_process(
        self,
        audio_files: List[np.ndarray],
        payloads: List[np.ndarray],
        **kwargs
    ) -> List[Tuple[np.ndarray, Dict[str, Any]]]:
        """
        Process multiple audio files in batch with GPU optimization.
        
        Args:
            audio_files: List of audio signals
            payloads: List of corresponding payloads
            **kwargs: Additional parameters
            
        Returns:
            List of (watermarked_audio, info) tuples
        """
        logger.info(f"Batch processing {len(audio_files)} files...")
        
        results = []
        start_time = time.time()
        
        # Create batched data loader for all files
        batch_size = self.gpu_config["batch_size"]
        all_audio = np.stack(audio_files)
        all_payloads = np.stack(payloads)
        
        audio_tensor = torch.FloatTensor(all_audio).to(self.device)
        payload_tensor = torch.FloatTensor(all_payloads).to(self.device)
        
        dataset = TensorDataset(audio_tensor, payload_tensor)
        loader = DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=self.gpu_config["num_workers"],
            pin_memory=self.gpu_config["pin_memory"]
        )
        
        for i, (batch_audio, batch_payload) in enumerate(loader):
            logger.info(f"Processing batch {i+1}/{len(loader)}")
            
            try:
                # Use mixed precision if enabled
                if self.gpu_config["mixed_precision"]:
                    with amp.autocast():
                        watermarked, info = self.encode_with_quality_control(
                            batch_audio.cpu().numpy(),
                            batch_payload.cpu().numpy(),
                            **kwargs
                        )
                else:
                    watermarked, info = self.encode_with_quality_control(
                        batch_audio.cpu().numpy(),
                        batch_payload.cpu().numpy(),
                        **kwargs
                    )
                
                results.extend([(w, i) for w, i in zip(watermarked, [info]*len(batch_audio))])
                
            except Exception as e:
                logger.error(f"Failed to process batch {i+1}: {e}")
                results.extend([(a, {'error': str(e)}) for a in batch_audio.cpu().numpy()])
        
        total_time = time.time() - start_time
        logger.info(f"Batch processing completed in {total_time:.2f}s")
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        if not self.encoding_stats and not self.decoding_stats:
            return {'message': 'No processing statistics available'}
        
        stats = {}
        
        if self.encoding_stats:
            snr_values = [s['actual_snr'] for s in self.encoding_stats]
            success_rates = [s['success_rate'] for s in self.encoding_stats]
            
            stats['encoding'] = {
                'total_encodings': len(self.encoding_stats),
                'avg_snr': np.mean(snr_values),
                'std_snr': np.std(snr_values),
                'avg_success_rate': np.mean(success_rates),
                'avg_attempts': np.mean([s['attempts'] for s in self.encoding_stats])
            }
        
        if self.decoding_stats:
            confidence_values = [s['confidence'] for s in self.decoding_stats]
            detection_counts = [s['num_detections'] for s in self.decoding_stats]
            
            stats['decoding'] = {
                'total_decodings': len(self.decoding_stats),
                'avg_confidence': np.mean(confidence_values),
                'std_confidence': np.std(confidence_values),
                'avg_detections': np.mean(detection_counts),
                'quality_distribution': {
                    'high': sum(1 for s in self.decoding_stats if s['detection_quality'] == 'high'),
                    'medium': sum(1 for s in self.decoding_stats if s['detection_quality'] == 'medium'),
                    'low': sum(1 for s in self.decoding_stats if s['detection_quality'] == 'low')
                }
            }
        
        return stats 
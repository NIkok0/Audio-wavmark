import os
import numpy as np
from scipy.io import wavfile
import wave
from .path_utils import get_user_dated_embed_dir

# 添加算法时前三个函数不用动，是自动调用的
import sys
import librosa
import soundfile as sf
from pathlib import Path
import torch
import shutil
import argparse
import time  # 添加time模块导入
from joblib import Parallel, delayed
import logging

# 添加wavmark模块到sys.path，保证无论从哪里运行都能找到
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
SRC_PATH = os.path.join(PROJECT_ROOT, 'watermark', 'utils', 'src')
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

logger = logging.getLogger(__name__)

print(SRC_PATH)

def extract(input_file, algorithm):
    """音频水印提取 - 支持多种算法（基于配置）"""
    # 获取文件扩展名
    _, extension = os.path.splitext(input_file)
    extension = extension[1:].lower()
    
    # 生成函数名 (格式: extract_扩展名_算法名)
    function_name = f"extract_{extension}_{algorithm.lower()}"
    
    try:
        # 获取当前模块中的函数
        extract_function = globals().get(function_name)
        if extract_function is None:
            raise ValueError(f"音频水印算法 {algorithm} 不支持 {extension} 格式")
        
        return extract_function(input_file)
        
    except Exception as e:
        print(f"音频水印提取算法 {algorithm} 失败: {str(e)}")
        raise

def extract_mp3_ai(input_file):
    """AI 算法音频水印提取和解码功能，输出载荷、BER、解码信息等"""
    try:
        # 加载音频
        audio, sr = load_audio_file(input_file)
        from wavmark import load_model, decode_watermark # type: ignore
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = load_model(device=device)
        if torch.cuda.is_available() and hasattr(torch, 'compile'):
            model = torch.compile(model)
        print("开始解码水印...")
        decoded_payload, decode_info = decode_watermark(model=model, signal=audio, show_progress=True, decode_batch_size=16)
        # 输出比特错误率等信息
        result = {
            'input_file': input_file,
            'decoded_payload': decoded_payload.tolist() if decoded_payload is not None else None,
            'ber': float(np.mean(decoded_payload != 0)) if decoded_payload is not None else None,
            'decode_info': decode_info
        }
        print(f"解码完成! BER: {result['ber']}")
        return to_serializable(result)
    except Exception as e:
        print(f"AI 算法音频水印提取失败: {str(e)}")
        return {'error': str(e)}

def extract_wav_ai(input_file):
    """AI 算法音频水印提取和解码功能，输出载荷、BER、解码信息等"""
    try:
        # 加载音频
        audio, sr = load_audio_file(input_file)
        from wavmark import load_model, decode_watermark # type: ignore
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = load_model(device=device)
        if torch.cuda.is_available() and hasattr(torch, 'compile'):
            model = torch.compile(model)
        print("开始解码水印...")
        decoded_payload, decode_info = decode_watermark(model=model, signal=audio, show_progress=True, decode_batch_size=16)
        # 输出比特错误率等信息
        result = {
            'input_file': input_file,
            'decoded_payload': decoded_payload.tolist() if decoded_payload is not None else None,
            'ber': float(np.mean(decoded_payload != 0)) if decoded_payload is not None else None,
            'decode_info': decode_info
        }
        print(f"解码完成! BER: {result['ber']}")
        return to_serializable(result)
    except Exception as e:
        print(f"AI 算法音频水印提取失败: {str(e)}")
        return {'error': str(e)}
    
def extract_flac_ai(input_file):
    """AI 算法音频水印提取和解码功能，输出载荷、BER、解码信息等"""
    try:
        # 加载音频
        audio, sr = load_audio_file(input_file)
        from wavmark import load_model, decode_watermark # type: ignore
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = load_model(device=device)
        if torch.cuda.is_available() and hasattr(torch, 'compile'):
            model = torch.compile(model)
        print("开始解码水印...")
        decoded_payload, decode_info = decode_watermark(model=model, signal=audio, show_progress=True, decode_batch_size=16)
        # 输出比特错误率等信息
        result = {
            'input_file': input_file,
            'decoded_payload': decoded_payload.tolist() if decoded_payload is not None else None,
            'ber': float(np.mean(decoded_payload != 0)) if decoded_payload is not None else None,
            'decode_info': decode_info
        }
        print(f"解码完成! BER: {result['ber']}")
        return to_serializable(result)
    except Exception as e:
        print(f"AI 算法音频水印提取失败: {str(e)}")
        return {'error': str(e)}
    
def extract_ogg_ai(input_file):
    """AI 算法音频水印提取和解码功能，输出载荷、BER、解码信息等"""
    try:
        # 加载音频
        audio, sr = load_audio_file(input_file)
        from wavmark import load_model, decode_watermark # type: ignore
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = load_model(device=device)
        if torch.cuda.is_available() and hasattr(torch, 'compile'):
            model = torch.compile(model)
        print("开始解码水印...")
        decoded_payload, decode_info = decode_watermark(model=model, signal=audio, show_progress=True, decode_batch_size=16)
        # 输出比特错误率等信息
        result = {
            'input_file': input_file,
            'decoded_payload': decoded_payload.tolist() if decoded_payload is not None else None,
            'ber': float(np.mean(decoded_payload != 0)) if decoded_payload is not None else None,
            'decode_info': decode_info
        }
        print(f"解码完成! BER: {result['ber']}")
        return to_serializable(result)
    except Exception as e:
        print(f"AI 算法音频水印提取失败: {str(e)}")
        return {'error': str(e)}

def extract_m4a_ai(input_file):
    """AI 算法音频水印提取和解码功能，输出载荷、BER、解码信息等"""
    try:
        # 加载音频
        audio, sr = load_audio_file(input_file)
        from wavmark import load_model, decode_watermark # type: ignore
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = load_model(device=device)
        if torch.cuda.is_available() and hasattr(torch, 'compile'):
            model = torch.compile(model)
        print("开始解码水印...")
        decoded_payload, decode_info = decode_watermark(model=model, signal=audio, show_progress=True, decode_batch_size=16)
        # 输出比特错误率等信息
        result = {
            'input_file': input_file,
            'decoded_payload': decoded_payload.tolist() if decoded_payload is not None else None,
            'ber': float(np.mean(decoded_payload != 0)) if decoded_payload is not None else None,
            'decode_info': decode_info
        }
        print(f"解码完成! BER: {result['ber']}")
        return to_serializable(result)
    except Exception as e:
        print(f"AI 算法音频水印提取失败: {str(e)}")
        return {'error': str(e)}

def extract_aac_ai(input_file):
    """AI 算法音频水印提取和解码功能，输出载荷、BER、解码信息等"""
    try:
        # 加载音频
        audio, sr = load_audio_file(input_file)
        from wavmark import load_model, decode_watermark # type: ignore
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = load_model(device=device)
        if torch.cuda.is_available() and hasattr(torch, 'compile'):
            model = torch.compile(model)
        print("开始解码水印...")
        decoded_payload, decode_info = decode_watermark(model=model, signal=audio, show_progress=True, decode_batch_size=16)
        # 输出比特错误率等信息
        result = {
            'input_file': input_file,
            'decoded_payload': decoded_payload.tolist() if decoded_payload is not None else None,
            'ber': float(np.mean(decoded_payload != 0)) if decoded_payload is not None else None,
            'decode_info': decode_info
        }
        print(f"解码完成! BER: {result['ber']}")
        return to_serializable(result)
    except Exception as e:
        print(f"AI 算法音频水印提取失败: {str(e)}")
        return {'error': str(e)}

def embed(input_file, watermark, algorithm):
    """音频水印嵌入 - 负责算法调用和文件保存"""
    
    # 获取文件扩展名
    _, extension = os.path.splitext(input_file)
    extension = extension[1:].lower()
    
    # 生成函数名 (格式: embed_扩展名_算法名)
    function_name = f"embed_{extension}_{algorithm.lower()}"
    
    try:
        # 获取当前模块中的函数
        embed_function = globals().get(function_name)
        if embed_function is None:
            raise ValueError(f"音频水印算法 {algorithm} 不支持 {extension} 格式")
        
        
        # 文件保存逻辑
        original_name = os.path.basename(input_file)
        name_without_ext = os.path.splitext(original_name)[0]
        filename = f"{name_without_ext}_embed.{extension}"
        
        # 从app.config获取保存路径 - 使用用户日期分层路径
        embed_dir = get_user_dated_embed_dir('audio')
        full_path = os.path.join(embed_dir, filename)

        # 调用算法，获取处理后的音频数据
        file_data,sr= embed_function(input_file,full_path, watermark)

        # 保存文件
        if file_data is None or sr is None:
            print("水印嵌入失败，未生成音频数据。")
            return None
        wavfile.write(full_path, sr, file_data)
        print(f"水印嵌入成功，保存到: {full_path}")
        return full_path  # 返回完整路径
    
    except Exception as e:
        print(f"音频水印算法 {algorithm} 失败: {str(e)}")
        raise

def setup_ffmpeg():
    """Setup ffmpeg path for audio processing."""
    try:
        # First try to find ffmpeg in PATH
        if shutil.which('ffmpeg'):
            ffmpeg_path = shutil.which('ffmpeg')
            print(f"Found ffmpeg in PATH: {ffmpeg_path}")
            return ffmpeg_path
            
        # Check common ffmpeg paths
        ffmpeg_paths = [
            os.path.join(os.path.expanduser("~"), "AppData", "Local", "ffmpegio", "ffmpeg-downloader", "ffmpeg", "bin"),
            r"C:\ffmpeg\bin",
            r"C:\Program Files\ffmpeg\bin",
            r"C:\Program Files (x86)\ffmpeg\bin"
        ]
        
        for path in ffmpeg_paths:
            ffmpeg_exe = os.path.join(path, "ffmpeg.exe")
            if os.path.exists(ffmpeg_exe):
                print(f"Found ffmpeg at: {ffmpeg_exe}")
                # Add to PATH
                os.environ["PATH"] = path + os.pathsep + os.environ["PATH"]
                return ffmpeg_exe
        
        print("Warning: ffmpeg not found in common locations")
        print("Audio format conversion may not work properly")
        return None
        
    except Exception as e:
        print(f"Error setting up ffmpeg: {e}")
        return None

# Setup ffmpeg before importing pydub
ffmpeg_path = setup_ffmpeg()

# Now import pydub and configure it
from pydub import AudioSegment

if ffmpeg_path:
    AudioSegment.converter = ffmpeg_path
    AudioSegment.ffmpeg = ffmpeg_path
    ffprobe_path = ffmpeg_path.replace('ffmpeg.exe', 'ffprobe.exe')
    if os.path.exists(ffprobe_path):
        AudioSegment.ffprobe = ffprobe_path
        print(f"Found ffprobe at: {ffprobe_path}")
    else:
        print(f"Warning: ffprobe not found at {ffprobe_path}")

def check_gpu():
    """Check if GPU is available."""
    if not torch.cuda.is_available():
        print("GPU not available! This program requires GPU to run.")
        sys.exit(1)
    print(f"GPU: {torch.cuda.get_device_name(0)}")

def display_payload_comparison(original_payload: np.ndarray, decoded_payload: np.ndarray, 
                             file_name: str = "Audio File"):
    """Display only BER and error bits info."""
    print(f"\n{'='*60}")
    print(f"水印载荷对比 - {file_name}")
    print(f"{'='*60}")
    if decoded_payload is not None:
        ber = np.mean(original_payload != decoded_payload)
        error_bits = np.sum(original_payload != decoded_payload)
        total_bits = len(original_payload)
        print(f"错误位数: {error_bits}/{total_bits}")
        print(f"比特错误率(BER): {ber:.3f} ({ber*100:.1f}%)")
        if ber == 0:
            print(f"\n✅ 完美匹配 - 水印解码成功!")
        elif ber <= 0.01:
            print(f"\n✅ 优秀质量 - 水印解码成功 (BER < 1%)")
        else:
            print(f"\n❌ 质量较差 - 水印解码失败 (BER >= 10%)")
    else:
        print(f"❌ 解码失败 - 无法提取水印载荷")
    print(f"{'='*60}")

def load_audio_file(file_path: str, target_sr: int = 16000) -> tuple[np.ndarray, int]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # 优先用 soundfile 读取 wav/flac
    if file_ext in ['.wav', '.flac']:
        try:
            audio, sr = sf.read(file_path)
            if sr != target_sr:
                import resampy
                audio = resampy.resample(audio, sr, target_sr)
                sr = target_sr
            if audio.ndim > 1:
                audio = audio[:, 0]
            # 音频长度保护
            if len(audio) < 1000:
                raise ValueError(f"音频文件过短或损坏: {file_path}")
            return audio, sr
        except Exception as e:
            print(f'soundfile 读取失败: {e}')
    
    # 尝试使用librosa
    try:
        print("尝试使用librosa读取...")
        audio, sr = librosa.load(file_path, sr=target_sr, mono=True)
        # 音频长度保护
        if len(audio) < 1000:
            raise ValueError(f"音频文件过短或损坏: {file_path}")
        return audio, sr
    except Exception as e:
        print(f"librosa 读取失败: {e}")
    
    # 最后尝试用 pydub
    try:
        from pydub import AudioSegment
        temp_wav = file_path + '.temp.wav'
        
        # 根据文件扩展名选择正确的加载方法
        if file_ext == '.mp3':
            audio = AudioSegment.from_mp3(file_path)
        elif file_ext == '.wav':
            audio = AudioSegment.from_wav(file_path)
        elif file_ext == '.ogg':
            audio = AudioSegment.from_ogg(file_path)
        elif file_ext == '.flac':
            audio = AudioSegment.from_file(file_path, "flac")
        else:
            audio = AudioSegment.from_file(file_path)
            
        print(f"pydub读取成功: duration={len(audio)}ms, channels={audio.channels}, frame_rate={audio.frame_rate}")
        
        # 转换为单声道、指定采样率、16位PCM
        audio = audio.set_channels(1)
        audio = audio.set_frame_rate(target_sr)
        audio = audio.set_sample_width(2)  # 16-bit
        
        try:
            # 导出为临时WAV文件
            audio.export(
                temp_wav,
                format='wav',
                parameters=[
                    "-acodec", "pcm_s16le",
                    "-ac", "1",
                    "-ar", str(target_sr)
                ]
            )
            
            # 使用soundfile读取转换后的文件
            audio_data, sr = sf.read(temp_wav)
            
            # 清理临时文件
            if os.path.exists(temp_wav):
                try:
                    os.remove(temp_wav)
                except Exception as e:
                    print(f"清理临时文件失败: {e}")
            
            # 音频长度保护
            if len(audio_data) < 1000:
                raise ValueError(f"音频文件过短或损坏: {file_path}")
                
            return audio_data, sr
            
        except Exception as e:
            print(f"处理转换后的WAV文件失败: {e}")
            if os.path.exists(temp_wav):
                try:
                    os.remove(temp_wav)
                except:
                    pass
            raise
            
    except Exception as e:
        print(f'pydub 读取失败: {e}')
        raise ValueError(f"无法读取音频文件 {file_path}: {str(e)}")

def save_audio_file(audio: np.ndarray, file_path: str, sr: int = 16000):
    """Save audio file in appropriate format."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext != '.wav':
        try:
            temp_dir = os.path.join(os.path.dirname(file_path), 'temp_audio')
            os.makedirs(temp_dir, exist_ok=True)
            temp_wav = os.path.join(temp_dir, "temp_output.wav")
            
            # Normalize audio
            audio = audio.astype(np.float32)
            if np.abs(audio).max() > 1.0:
                audio = audio / np.abs(audio).max()
            audio_int16 = (audio * 32767).astype(np.int16)
            
            sf.write(temp_wav, audio_int16, sr, subtype='PCM_16')
            audio_segment = AudioSegment.from_wav(temp_wav)
            
            # Format mapping
            format_map = {
                '.mp3': ('mp3', 'libmp3lame'),
                '.m4a': ('ipod', 'aac'),
                '.aac': ('adts', 'aac'),
                '.ogg': ('ogg', 'libvorbis'),
                '.flac': ('flac', 'flac')
            }
            
            output_format, codec = format_map.get(file_ext, ('wav', None))
            export_params = {
                'format': output_format,
                'codec': codec,
                'parameters': ["-b:a", "192k"] if codec in ['aac', 'libmp3lame'] else None
            }
            export_params = {k: v for k, v in export_params.items() if v is not None}
            audio_segment.export(file_path, **export_params)
            shutil.rmtree(temp_dir, ignore_errors=True)
            
        except Exception as e:
            print(f"Format conversion failed: {e}")
            wav_path = os.path.splitext(file_path)[0] + '.wav'
            sf.write(wav_path, audio, sr)
    else:
        sf.write(file_path, audio, sr)

def process_audio_file(input_file: str, output_file: str = None, watermark = None,
                      show_comparison: bool = False) -> tuple[bool, dict]:
    """Process single audio file with watermark. 只做嵌入，不再解码和比对。"""
    try:
        print(f"\n处理文件: {input_file}")
        audio, sr = load_audio_file(input_file)

        # 处理载荷
        s = str(watermark).strip()
        print(f"收到的watermark原始值: {s}")
        if s == '1':
            payload_arr = np.random.randint(0, 2, 16)
            print(f"使用随机载荷: {payload_arr}")
        else:
            # 支持16位二进制字符串、逗号或空格分隔
            valid = False
            if len(s) == 16 and all(c in '01' for c in s):
                payload_arr = np.array([int(c) for c in s])
                valid = True
            else:
                for sep in [',', ' ']:
                    if sep in s:
                        values = [int(x.strip()) for x in s.split(sep)]
                        if len(values) == 16 and all(x in [0, 1] for x in values):
                            payload_arr = np.array(values)
                            valid = True
                            break
            if not valid:
                raise ValueError("无效的载荷格式，请输入'1'或16位01数组")
            print(f"使用自定义载荷: {payload_arr}")

        from wavmark import load_model, encode_watermark # type: ignore
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = load_model(device=device)
        if torch.cuda.is_available() and hasattr(torch, 'compile'):
            model = torch.compile(model)
        print("开始编码水印...")
        watermarked_audio, encode_info = encode_watermark(
            model=model,
            signal=audio,
            payload=payload_arr,
            min_snr=25.0,
            max_snr=35.0,
            show_progress=True
        )
        if output_file is None:
            output_file = str(Path(input_file).parent / f"{Path(input_file).stem}_watermarked{Path(input_file).suffix}")
        print(f"保存水印音频: {output_file}")
        save_audio_file(watermarked_audio, output_file, sr)
        result = {
            'input_file': input_file,
            'output_file': output_file,
            'payload': payload_arr,
            'snr': encode_info['snr']
        }
        print(f"处理完成! SNR: {encode_info['snr']:.1f} dB")
        return True, result
    except Exception as e:
        print(f"处理失败: {e}")
        return False, None

def batch_process_from_directories(input_dir: str, output_dir: str, payload: np.ndarray = None, 
                                 show_comparison: bool = True) -> tuple[bool, list]:
    """Batch process audio files from directory (串行处理)."""
    try:
        if not os.path.exists(input_dir):
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
        os.makedirs(output_dir, exist_ok=True)
        # Find all audio files
        audio_files = set()
        for ext in ['.wav', '.mp3', '.flac', '.m4a', '.ogg', '.aac']:
            audio_files.update(str(f) for f in Path(input_dir).glob(f"*{ext}"))
            audio_files.update(str(f) for f in Path(input_dir).glob(f"*{ext.upper()}"))
        audio_files = sorted(list(audio_files))
        if not audio_files:
            print("未找到音频文件!")
            return False, []
        print(f"找到 {len(audio_files)} 个音频文件")
        if payload is not None:
            print(f"将使用统一载荷: {payload}")
        results = []
        for file in audio_files:
            output_file = os.path.join(output_dir, f"{Path(file).stem}_watermarked{Path(file).suffix}")
            success, result = process_audio_file(file, output_file, payload, show_comparison)
            if success:
                results.append(result)
        return True, results
    except Exception as e:
        print(f"批量处理失败: {e}")
        return False, []

def embed_mp3_ai(input_file, output_file, watermark):
    """Main function for WavMark 音频水印处理工具（仅水印嵌入）"""
    # Check GPU
    #check_gpu()

    # 直接用传入的 watermark
    payload = watermark
    # Process files
    if os.path.isfile(input_file):
        # Single file processing
        success, result = process_audio_file(input_file, None, payload, False)  # 不比对载荷
        if success and result is not None:
            print(f"\n✅ 文件处理成功!")
            print(f"输出文件: {result['output_file']}")
            # 需要返回处理后的音频数据和采样率
            audio, sr = load_audio_file(result['output_file'])
            return audio, sr
        else:
            print(f"\n❌ 文件处理失败!")
            return None, None
    else:
        # Batch processing
        success, results = batch_process_from_directories(input_file, output_file, payload, False)
        if success:
            print(f"\n✅ 批量处理完成!")
            if results:
                print(f"成功处理 {len(results)} 个文件")
                print(f"输出目录: {output_file}")
            else:
                print("没有文件被处理")
        else:
            print(f"\n❌ 批量处理失败!")
        return None, None

def embed_wav_ai(input_file, output_file, watermark):
    """Main function for WavMark 音频水印处理工具（仅水印嵌入）"""
    # Check GPU
    #check_gpu()

    # 直接用传入的 watermark
    payload = watermark
    # Process files
    if os.path.isfile(input_file):
        # Single file processing
        success, result = process_audio_file(input_file, None, payload, False)  # 不比对载荷
        if success and result is not None:
            print(f"\n✅ 文件处理成功!")
            print(f"输出文件: {result['output_file']}")
            # 需要返回处理后的音频数据和采样率
            audio, sr = load_audio_file(result['output_file'])
            return audio, sr
        else:
            print(f"\n❌ 文件处理失败!")
            return None, None
    else:
        # Batch processing
        success, results = batch_process_from_directories(input_file, output_file, payload, False)
        if success:
            print(f"\n✅ 批量处理完成!")
            if results:
                print(f"成功处理 {len(results)} 个文件")
                print(f"输出目录: {output_file}")
            else:
                print("没有文件被处理")
        else:
            print(f"\n❌ 批量处理失败!")
        return None, None

def embed_flac_ai(input_file, output_file, watermark):
    """Main function for WavMark 音频水印处理工具（仅水印嵌入）"""
    # Check GPU
    #check_gpu()

    # 直接用传入的 watermark
    payload = watermark
    # Process files
    if os.path.isfile(input_file):
        # Single file processing
        success, result = process_audio_file(input_file, None, payload, False)  # 不比对载荷
        if success and result is not None:
            print(f"\n✅ 文件处理成功!")
            print(f"输出文件: {result['output_file']}")
            # 需要返回处理后的音频数据和采样率
            audio, sr = load_audio_file(result['output_file'])
            return audio, sr
        else:
            print(f"\n❌ 文件处理失败!")
            return None, None
    else:
        # Batch processing
        success, results = batch_process_from_directories(input_file, output_file, payload, False)
        if success:
            print(f"\n✅ 批量处理完成!")
            if results:
                print(f"成功处理 {len(results)} 个文件")
                print(f"输出目录: {output_file}")
            else:
                print("没有文件被处理")
        else:
            print(f"\n❌ 批量处理失败!")
        return None, None

def embed_aac_ai(input_file, output_file, watermark):
    """Main function for WavMark 音频水印处理工具（仅水印嵌入）"""
    # Check GPU
    #check_gpu()

    # 直接用传入的 watermark
    payload = watermark
    # Process files
    if os.path.isfile(input_file):
        # Single file processing
        success, result = process_audio_file(input_file, None, payload, False)  # 不比对载荷
        if success and result is not None:
            print(f"\n✅ 文件处理成功!")
            print(f"输出文件: {result['output_file']}")
            # 需要返回处理后的音频数据和采样率
            audio, sr = load_audio_file(result['output_file'])
            return audio, sr
        else:
            print(f"\n❌ 文件处理失败!")
            return None, None
    else:
        # Batch processing
        success, results = batch_process_from_directories(input_file, output_file, payload, False)
        if success:
            print(f"\n✅ 批量处理完成!")
            if results:
                print(f"成功处理 {len(results)} 个文件")
                print(f"输出目录: {output_file}")
            else:
                print("没有文件被处理")
        else:
            print(f"\n❌ 批量处理失败!")
        return None, None

def embed_m4a_ai(input_file, output_file, watermark):
    """Main function for WavMark 音频水印处理工具（仅水印嵌入）"""
    # Check GPU
   

    # 直接用传入的 watermark
    payload = watermark
    # Process files
    if os.path.isfile(input_file):
        # Single file processing
        success, result = process_audio_file(input_file, None, payload, False)  # 不比对载荷
        if success and result is not None:
            print(f"\n✅ 文件处理成功!")
            print(f"输出文件: {result['output_file']}")
            # 需要返回处理后的音频数据和采样率
            audio, sr = load_audio_file(result['output_file'])
            return audio, sr
        else:
            print(f"\n❌ 文件处理失败!")
            return None, None
    else:
        # Batch processing
        success, results = batch_process_from_directories(input_file, output_file, payload, False)
        if success:
            print(f"\n✅ 批量处理完成!")
            if results:
                print(f"成功处理 {len(results)} 个文件")
                print(f"输出目录: {output_file}")
            else:
                print("没有文件被处理")
        else:
            print(f"\n❌ 批量处理失败!")
        return None, None

def embed_ogg_ai(input_file, output_file, watermark):
    """Main function for WavMark 音频水印处理工具（仅水印嵌入）"""
    # Check GPU
    #check_gpu()

    # 直接用传入的 watermark
    payload = watermark
    # Process files
    if os.path.isfile(input_file):
        # Single file processing
        success, result = process_audio_file(input_file, None, payload, False)  # 不比对载荷
        if success and result is not None:
            print(f"\n✅ 文件处理成功!")
            print(f"输出文件: {result['output_file']}")
            # 需要返回处理后的音频数据和采样率
            audio, sr = load_audio_file(result['output_file'])
            return audio, sr
        else:
            print(f"\n❌ 文件处理失败!")
            return None, None
    else:
        # Batch processing
        success, results = batch_process_from_directories(input_file, output_file, payload, False)
        if success:
            print(f"\n✅ 批量处理完成!")
            if results:
                print(f"成功处理 {len(results)} 个文件")
                print(f"输出目录: {output_file}")
            else:
                print("没有文件被处理")
        else:
            print(f"\n❌ 批量处理失败!")
        return None, None
    
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

def to_serializable(obj):
    if isinstance(obj, np.generic):
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [to_serializable(i) for i in obj]
    else:
        return obj


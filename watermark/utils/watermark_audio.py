# Standard library imports
import os

# Third-party imports
import numpy as np
from scipy.io import wavfile
import wave
from flask import current_app

# 添加算法时前三个函数不用动，是自动调用的



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
        
        # 调用算法，获取处理后的音频数据
        file_data = embed_function(input_file, watermark)
        
        # 文件保存逻辑
        original_name = os.path.basename(input_file)
        name_without_ext = os.path.splitext(original_name)[0]
        filename = f"{name_without_ext}_embed.{extension}"
        
        # 从app.config获取保存路径
        embed_dir = current_app.config['MEDIA_FOLDERS']['audio']['embed']
        full_path = os.path.join(embed_dir, filename)
        
        # 保存文件
        with open(full_path, 'wb') as f:
            f.write(file_data)
        
        return full_path  # 返回完整路径
        
    except Exception as e:
        print(f"音频水印算法 {algorithm} 失败: {str(e)}")
        raise

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

def embed_ogg_lsb(input_file, watermark):
    """LSB算法实现 - OGG音频LSB隐写"""
    print("audio_watermark_embed for OGG!")
    with open(input_file, 'rb') as file:
        return file.read()  # 直接返回文件内容

def extract_ogg_lsb(input_file):
    """LSB算法提取 - OGG音频LSB隐写"""
    print("audio_watermark_extract for OGG!")
    return "test"

def embed_wav_lsb(input_file, watermark):
    """LSB算法实现 - WAV音频LSB隐写"""
    print("audio_watermark_embed for WAV!")
    
    # 读取音频文件
    sample_rate, audio_data = wavfile.read(input_file)
    
    
    return audio_data

def extract_wav_lsb(input_file):
    result = "test"
    return result

# 为MP3格式添加LSB算法实现
def embed_mp3_lsb(input_file, watermark):
    """LSB算法实现 - MP3音频LSB隐写"""
    raise NotImplementedError("MP3格式的LSB水印算法尚未实现")

def extract_mp3_lsb(input_file):
    """LSB算法提取 - MP3音频LSB水印提取"""
    raise NotImplementedError("MP3格式的LSB水印提取算法尚未实现")



def embed_wav_dct(input_file, watermark):
    """DCT算法实现 - WAV格式专用"""
    raise NotImplementedError("WAV格式的DCT水印算法尚未实现")

def extract_wav_dct(input_file):
    """DCT算法提取 - WAV格式专用"""
    raise NotImplementedError("WAV格式的DCT水印提取算法尚未实现")

def embed_mp3_dct(input_file, watermark):
    """DCT算法实现 - MP3格式专用"""
    raise NotImplementedError("MP3格式的DCT水印算法尚未实现")

def extract_mp3_dct(input_file):
    """DCT算法提取 - MP3格式专用"""
    raise NotImplementedError("MP3格式的DCT水印提取算法尚未实现")



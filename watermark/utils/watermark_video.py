FFMPEG_BIN = "ffmpeg.exe"

import subprocess as sp
import numpy
import watermark.utils.robust as robust
import os
import json
import cv2
import numpy as np
from PIL import Image
from flask import current_app

def bin_value(value, bitsize):
    """将整数转化为固定长度的二进制字符串"""
    binval = bin(value)[2:]
    if len(binval) > bitsize:
        print("Too Large!")
    while len(binval) < bitsize:
        binval = "0" + binval
    return binval

def get_video_info(video_path):
    """获取视频信息，包括分辨率"""
    try:
        command = [FFMPEG_BIN, 
                  '-i', video_path, 
                  '-v', 'error',
                  '-select_streams', 'v:0', 
                  '-show_entries', 'stream=width,height,pix_fmt', 
                  '-of', 'json']
        
        result = sp.run(command, stdout=sp.PIPE, stderr=sp.PIPE)
        video_info = json.loads(result.stdout)
        
        width = int(video_info['streams'][0]['width'])
        height = int(video_info['streams'][0]['height'])
        pix_fmt = video_info['streams'][0]['pix_fmt'] if 'pix_fmt' in video_info['streams'][0] else 'yuv420p'
        
        # 确保分辨率是8的倍数，方便DCT处理
        width = (width // 8) * 8
        height = (height // 8) * 8
        
        return width, height, pix_fmt
    except Exception as e:
        print(f"获取视频信息失败: {str(e)}")
        # 返回默认分辨率
        return 1920, 1080, 'yuv420p'

def embed(input_file, watermark, algorithm):
    """视频水印嵌入 - 负责算法调用和文件保存"""
    
    # 直接生成函数名
    function_name = f"embed_{algorithm.lower()}"
    
    try:
        # 获取当前模块中的函数
        embed_function = globals().get(function_name)
        if embed_function is None:
            raise ValueError(f"视频水印算法 {algorithm} 的实现函数 {function_name} 不存在")
        
        # 调用算法，获取处理后的视频对象
        processed_video = embed_function(input_file, watermark)
        
        # 文件保存逻辑
        original_name = os.path.basename(input_file)
        name_without_ext = os.path.splitext(original_name)[0]
        filename = f"{name_without_ext}_embed.mp4"
        
        # 从app.config获取保存路径
        embed_dir = current_app.config['MEDIA_FOLDERS']['video']['embed']
        full_path = os.path.join(embed_dir, filename)
        
        # 保存文件 - 在这种情况下，processed_video已经是保存好的文件路径
        # 因为视频处理过程中需要直接写入文件
        if os.path.exists(processed_video) and processed_video != full_path:
            os.rename(processed_video, full_path)
        
        return full_path  # 返回完整路径
        
    except Exception as e:
        print(f"视频水印算法 {algorithm} 失败: {str(e)}")
        raise

def extract(input_file, algorithm):
    """视频水印提取 - 支持多种算法（基于配置）"""
    # 直接生成函数名
    function_name = f"extract_{algorithm.lower()}"
    
    try:
        # 获取当前模块中的函数
        extract_function = globals().get(function_name)
        if extract_function is None:
            raise ValueError(f"视频水印算法 {algorithm} 的提取函数 {function_name} 不存在")
        
        return extract_function(input_file)
        
    except Exception as e:
        print(f"视频水印提取算法 {algorithm} 失败: {str(e)}")
        raise

def embed_dct(input_file, watermark):
    print("video_watermark_embed!")
    return input_file


def extract_dct(input_file):
    print("video_watermark_extract!")
    return "test"

def embed_cox(input_file, watermark):
    """Cox算法实现 - 后期实现"""
    raise NotImplementedError("视频Cox算法尚未实现")

def embed_lsb(input_file, watermark):
    """LSB算法实现 - 后期实现"""
    raise NotImplementedError("视频LSB算法尚未实现")

def embed_dwt(input_file, watermark):
    """DWT算法实现 - 后期实现"""
    raise NotImplementedError("视频DWT算法尚未实现")

def extract_cox(input_file):
    """Cox算法提取 - 后期实现"""
    raise NotImplementedError("视频Cox算法尚未实现")

def extract_lsb(input_file):
    """LSB算法提取 - 后期实现"""
    raise NotImplementedError("视频LSB算法尚未实现")

def extract_dwt(input_file):
    """DWT算法提取 - 后期实现"""
    raise NotImplementedError("视频DWT算法尚未实现")






import os
import numpy as np
from scipy.io import wavfile
import wave
from flask import current_app

# 添加算法时前三个函数不用动，是自动调用的


def bin_value(value, bitsize):
    """将整数转化为固定长度的二进制字符串"""
    binval = bin(value)[2:]
    if len(binval) > bitsize:
        print("Too Large!")
    while len(binval) < bitsize:
        binval = "0" + binval
    return binval

def embed(input_file, watermark, algorithm):
    """音频水印嵌入 - 负责算法调用和文件保存"""
    
    # 直接生成函数名
    function_name = f"embed_{algorithm.lower()}"
    
    try:
        # 获取当前模块中的函数
        embed_function = globals().get(function_name)
        if embed_function is None:
            raise ValueError(f"音频水印算法 {algorithm} 的实现函数 {function_name} 不存在")
        
        # 调用算法，获取处理后的音频数据和采样率
        processed_audio, sample_rate = embed_function(input_file, watermark)
        
        # 文件保存逻辑
        original_name = os.path.basename(input_file)
        name_without_ext = os.path.splitext(original_name)[0]
        filename = f"{name_without_ext}_embed.wav"
        
        # 从app.config获取保存路径
        embed_dir = current_app.config['MEDIA_FOLDERS']['audio']['embed']
        full_path = os.path.join(embed_dir, filename)
        
        # 保存文件
        wavfile.write(full_path, sample_rate, processed_audio.astype(np.int16))
        
        return full_path  # 返回完整路径
        
    except Exception as e:
        print(f"音频水印算法 {algorithm} 失败: {str(e)}")
        raise

def extract(input_file, algorithm):
    """音频水印提取 - 支持多种算法（基于配置）"""
    # 直接生成函数名
    function_name = f"extract_{algorithm.lower()}"
    
    try:
        # 获取当前模块中的函数
        extract_function = globals().get(function_name)
        if extract_function is None:
            raise ValueError(f"音频水印算法 {algorithm} 的提取函数 {function_name} 不存在")
        
        return extract_function(input_file)
        
    except Exception as e:
        print(f"音频水印提取算法 {algorithm} 失败: {str(e)}")
        raise





def embed_lsb(input_file, watermark):
    """LSB算法实现 - 音频LSB隐写"""
    print("audio_watermark_embed!")
    
    # 读取音频文件
    sample_rate, audio_data = wavfile.read(input_file)
    
    # 确保音频数据是整数类型
    if audio_data.dtype != np.int16:
        audio_data = audio_data.astype(np.int16)
    
    # 将音频数据转换为一维数组
    audio_flatten = audio_data.flatten()
    
    # 将水印字符串转换为UTF-8编码的字节
    data_bytes = watermark.encode('utf-8')
    data_length = len(data_bytes)
    
    # 检查音频容量是否足够
    if len(audio_flatten) < 32 + data_length * 8:
        raise ValueError(f"音频容量不足，无法嵌入长度为{data_length}字节的水印")
    
    # 存储长度信息（32位）
    bindata = bin_value(data_length, 32)
    
    # 嵌入长度信息
    index = 0
    for c in bindata:
        if int(c) == 0:
            audio_flatten[index] = audio_flatten[index] & 0xFFFE  # 清除最低位
        else:
            audio_flatten[index] = audio_flatten[index] | 0x0001  # 设置最低位
        index += 1
    
    # 嵌入水印内容
    for byte in data_bytes:
        for c in bin_value(byte, 8):
            if int(c) == 0:
                audio_flatten[index] = audio_flatten[index] & 0xFFFE
            else:
                audio_flatten[index] = audio_flatten[index] | 0x0001
            index += 1
    
    # 重塑音频数据
    if len(audio_data.shape) == 2:  # 立体声
        audio_embed = audio_flatten.reshape(audio_data.shape)
    else:  # 单声道
        audio_embed = audio_flatten
    
    return audio_embed, sample_rate

def extract_lsb(input_file):
    """LSB算法提取 - 音频LSB水印提取"""
    print("audio_watermark_extract!")
    
    # 读取音频文件
    sample_rate, audio_data = wavfile.read(input_file)
    
    # 将音频数据转换为一维数组
    audio_flatten = audio_data.flatten()
    
    # 提取水印长度（32位）
    str_length = ''
    index = 0
    while index < 32:
        if audio_flatten[index] & 0x0001:
            str_length += '1'
        else:
            str_length += '0'
        index += 1
    
    length = int(str_length, 2)
    
    # 提取水印字节
    bytes_data = bytearray()
    for i in range(length):
        byte_value = 0
        for bit_position in range(8):
            bit = 0
            if audio_flatten[index] & 0x0001:
                bit = 1
            byte_value = (byte_value << 1) | bit
            index += 1
        bytes_data.append(byte_value)
    
    # 将字节转换回UTF-8字符串
    try:
        result = bytes_data.decode('utf-8')
    except UnicodeDecodeError:
        result = "水印解码失败，可能是损坏的数据"
    
    print(result)
    return result

def embed_dct(input_file, watermark):
    """DCT算法实现 - 后期实现"""
    raise NotImplementedError("音频DCT算法尚未实现")

def embed_cox(input_file, watermark):
    """Cox算法实现 - 后期实现"""
    raise NotImplementedError("音频Cox算法尚未实现")

def extract_dct(input_file):
    """DCT算法提取 - 后期实现"""
    raise NotImplementedError("音频DCT算法尚未实现")

def extract_cox(input_file):
    """Cox算法提取 - 后期实现"""
    raise NotImplementedError("音频Cox算法尚未实现")


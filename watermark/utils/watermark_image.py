# Standard library imports
import os

# Third-party imports
import numpy as np
from PIL import Image
from flask import current_app


def embed(input_file, watermark, algorithm):
    """图像水印嵌入 - 负责算法调用和文件保存"""
    
    # 获取文件扩展名
    _, extension = os.path.splitext(input_file)
    extension = extension[1:].lower()
    
    # 生成函数名 (格式: embed_扩展名_算法名)
    function_name = f"embed_{extension}_{algorithm.lower()}"
    
    try:
        # 获取当前模块中的函数
        embed_function = globals().get(function_name)
        if embed_function is None:
            raise ValueError(f"图像水印算法 {algorithm} 不支持 {extension} 格式")
        
        # 调用算法，获取处理后的图像对象
        processed_image = embed_function(input_file, watermark)
        
        # 文件保存逻辑
        original_name = os.path.basename(input_file)
        name_without_ext = os.path.splitext(original_name)[0]
        filename = f"{name_without_ext}_embed.{extension}"
        
        # 从app.config获取保存路径
        embed_dir = current_app.config['MEDIA_FOLDERS']['image']['embed']
        full_path = os.path.join(embed_dir, filename)
        
        # 保存文件
        processed_image.save(full_path)
        
        return full_path  # 返回完整路径
        
    except Exception as e:
        print(f"图像水印算法 {algorithm} 失败: {str(e)}")
        raise

def extract(input_file, algorithm):
    """图像水印提取 - 支持多种算法（基于配置）"""
    # 获取文件扩展名
    _, extension = os.path.splitext(input_file)
    extension = extension[1:].lower()
    
    # 生成函数名 (格式: extract_扩展名_算法名)
    function_name = f"extract_{extension}_{algorithm.lower()}"
    
    try:
        # 获取当前模块中的函数
        extract_function = globals().get(function_name)
        if extract_function is None:
            raise ValueError(f"图像水印算法 {algorithm} 不支持 {extension} 格式")
        
        return extract_function(input_file)
        
    except Exception as e:
        print(f"图像水印提取算法 {algorithm} 失败: {str(e)}")
        raise

# 具体算法实现 - BMP格式
def embed_bmp_lsb(input_file, watermark):
    """使用 LSB 算法在 BMP 图像中嵌入水印"""
    # 打开图像
    img = Image.open(input_file)
    # 转换为 RGB 模式（如果不是的话）
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # 获取图像数据
    pixels = np.array(img)
    
    # 将水印文本转换为二进制
    watermark_bits = ''.join(format(ord(c), '08b') for c in watermark)
    watermark_length = len(watermark_bits)
    
    # 检查图像容量是否足够
    if watermark_length > pixels.size:
        raise ValueError("水印太长，图像容量不足")
    
    # 在图像的最低有效位嵌入水印
    bit_index = 0
    for i in range(pixels.shape[0]):
        for j in range(pixels.shape[1]):
            for k in range(pixels.shape[2]):
                if bit_index < watermark_length:
                    # 修改最低有效位
                    pixels[i, j, k] = (pixels[i, j, k] & ~1) | int(watermark_bits[bit_index])
                    bit_index += 1
                else:
                    break
            if bit_index >= watermark_length:
                break
        if bit_index >= watermark_length:
            break
    
    # 创建新图像
    processed_image = Image.fromarray(pixels)
    return processed_image

# JPG格式的LSB实现
def embed_jpg_lsb(input_file, watermark):
    """使用 LSB 算法在 JPG 图像中嵌入水印"""
    # 由于 JPG 的有损压缩特性，先将其转换为 BMP
    img = Image.open(input_file)
    return embed_bmp_lsb(img, watermark)

# PNG格式的LSB实现
def embed_png_lsb(input_file, watermark):
    """使用 LSB 算法在 PNG 图像中嵌入水印"""
    # PNG 可以直接使用 BMP 的实现
    return embed_bmp_lsb(input_file, watermark)

# 提取实现
def extract_bmp_lsb(input_file):
    return "test"
def extract_jpg_lsb(input_file):
    return "test"

def extract_png_lsb(input_file):
    return "test"

# DCT算法实现
def embed_jpg_dct(input_file, watermark):
    """DCT算法实现 - JPG格式专用"""
    raise NotImplementedError("JPG格式的DCT水印算法尚未实现")

def extract_jpg_dct(input_file):
    """DCT算法提取 - JPG格式专用"""
    raise NotImplementedError("JPG格式的DCT水印提取算法尚未实现")

def embed_bmp_dct(input_file, watermark):
    """DCT算法实现 - BMP格式专用"""
    raise NotImplementedError("BMP格式的DCT水印算法尚未实现")

def extract_bmp_dct(input_file):
    """DCT算法提取 - BMP格式专用"""
    raise NotImplementedError("BMP格式的DCT水印提取算法尚未实现")

# Cox算法实现
def embed_jpg_cox(input_file, watermark):
    """Cox算法实现 - JPG格式专用"""
    raise NotImplementedError("JPG格式的Cox水印算法尚未实现")

def extract_jpg_cox(input_file):
    """Cox算法提取 - JPG格式专用"""
    raise NotImplementedError("JPG格式的Cox水印提取算法尚未实现")

def embed_bmp_cox(input_file, watermark):
    """Cox算法实现 - BMP格式专用"""
    raise NotImplementedError("BMP格式的Cox水印算法尚未实现")

def extract_bmp_cox(input_file):
    """Cox算法提取 - BMP格式专用"""
    raise NotImplementedError("BMP格式的Cox水印提取算法尚未实现")

# DWT算法实现
def embed_jpg_dwt(input_file, watermark):
    """DWT算法实现 - JPG格式专用"""
    raise NotImplementedError("JPG格式的DWT水印算法尚未实现")

def extract_jpg_dwt(input_file):
    """DWT算法提取 - JPG格式专用"""
    raise NotImplementedError("JPG格式的DWT水印提取算法尚未实现")

def embed_bmp_dwt(input_file, watermark):
    """DWT算法实现 - BMP格式专用"""
    raise NotImplementedError("BMP格式的DWT水印算法尚未实现")

def extract_bmp_dwt(input_file):
    """DWT算法提取 - BMP格式专用"""
    raise NotImplementedError("BMP格式的DWT水印提取算法尚未实现")
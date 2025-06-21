from PIL import Image
from numpy import *
import os
from flask import current_app

# 嵌入水印
def bin_value(value, bitsize):
    """将整数转化为固定长度的二进制字符串"""
    binval = bin(value)[2:]
    if len(binval) > bitsize:
        print("Too Large!")
    while len(binval) < bitsize:
        binval = "0" + binval
    return binval

def embed(input_file, watermark, algorithm):
    """图像水印嵌入 - 负责算法调用和文件保存"""

    # 直接生成函数名
    function_name = f"embed_{algorithm.lower()}"
    
    try:
        # 获取当前模块中的函数
        embed_function = globals().get(function_name)
        if embed_function is None:
            raise ValueError(f"图像水印算法 {algorithm} 的实现函数 {function_name} 不存在")
        
        # 调用算法，获取处理后的图像对象
        processed_image = embed_function(input_file, watermark)
        
        # 文件保存逻辑
        original_name = os.path.basename(input_file)
        name_without_ext = os.path.splitext(original_name)[0]
        filename = f"{name_without_ext}_embed.bmp"
        
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
    # 直接生成函数名
    function_name = f"extract_{algorithm.lower()}"
    
    try:
        # 获取当前模块中的函数
        extract_function = globals().get(function_name)
        if extract_function is None:
            raise ValueError(f"图像水印算法 {algorithm} 的提取函数 {function_name} 不存在")
        
        return extract_function(input_file)
        
    except Exception as e:
        print(f"图像水印提取算法 {algorithm} 失败: {str(e)}")
        raise

# 具体算法实现
def embed_lsb(input_file, watermark):
    """LSB算法实现 - 只处理算法，不保存文件"""
    print("image_watermark_embed!")
    im = Image.open(input_file)
    im = im.convert('L')  # 转化为灰度图片
    
    # 为了避免压缩影响，先转换为BMP格式处理
    temp_file = "temp_processing.bmp"
    im.save(temp_file)
    im = Image.open(temp_file)

    im_array = array(im)  # 转化为数组
    row, col = im_array.shape
    im_array_flatten = im_array.flatten()  # 转化为一位数组

    # 将水印字符串转换为UTF-8编码的字节
    data_bytes = watermark.encode('utf-8')
    data_length = len(data_bytes)
    
    # 检查图像容量是否足够
    if row * col < 32 + data_length * 8:
        # 清理临时文件
        try:
            os.remove(temp_file)
        except:
            pass
        raise ValueError(f"图像容量不足，无法嵌入长度为{data_length}字节的水印")
        
    bindata = bin_value(data_length, 32)  # 使用32位来存储长度

    index = 0
    for c in bindata:  # 把长度嵌入
        if int(c) == 0:
            im_array_flatten[index] = im_array_flatten[index] & 254
        else:
            im_array_flatten[index] = im_array_flatten[index] | 1
        index += 1

    for byte in data_bytes:  # 把内容嵌入
        for c in bin_value(byte, 8):
            if int(c) == 0:
                im_array_flatten[index] = im_array_flatten[index] & 254
            else:
                im_array_flatten[index] = im_array_flatten[index] | 1
            index += 1

    # 重构图像
    image_array_embed = reshape(im_array_flatten, (row, col))
    im_embed = Image.fromarray(image_array_embed)
    
    # 清理临时文件
    try:
        os.remove(temp_file)
    except:
        pass
    
    # 只返回处理后的图像对象，不保存文件
    return im_embed

def extract_lsb(input_file):
    """LSB算法提取 - 已实现"""
    print("image_watermark_extract!")
    im = Image.open(input_file)
    im_array = array(im)  # 转化为数组
    im_array_flatten = im_array.flatten()  # 转化为一位数组
    
    # 提取水印长度（32位）
    str_length = ''
    index = 0
    while index < 32:
        if im_array_flatten[index] == im_array_flatten[index] & 254:
            str_length = str_length + '0'
        else:
            str_length = str_length + '1'
        index += 1

    length = int(str_length, 2)
    
    # 提取水印字节
    bytes_data = bytearray()
    for i in range(length):
        byte_value = 0
        for bit_position in range(8):
            bit = 0
            if im_array_flatten[index] & 1:
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
    raise NotImplementedError("DCT算法尚未实现")

def embed_cox(input_file, watermark):
    """Cox算法实现 - 后期实现"""
    raise NotImplementedError("Cox算法尚未实现")

def embed_dwt(input_file, watermark):
    """DWT算法实现 - 后期实现"""
    raise NotImplementedError("DWT算法尚未实现")

def extract_dct(input_file):
    """DCT算法实现 - 后期实现"""
    raise NotImplementedError("DCT算法尚未实现")

def extract_cox(input_file):
    """Cox算法实现 - 后期实现"""
    raise NotImplementedError("Cox算法尚未实现")

def extract_dwt(input_file):
    """DWT算法实现 - 后期实现"""
    raise NotImplementedError("DWT算法尚未实现")
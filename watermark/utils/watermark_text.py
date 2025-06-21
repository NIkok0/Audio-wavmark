import os
from flask import current_app

def bin_value(value, bitsize):
    """将整数转化为固定长度的二进制字符串"""
    binval = bin(value)[2:]
    if len(binval) > bitsize:
        print("Too Large!")
    while len(binval) < bitsize:
        binval = "0" + binval
    return binval

def embed(input_file, watermark, algorithm):
    """文本水印嵌入 - 负责算法调用和文件保存"""
    
    # 直接生成函数名
    function_name = f"embed_{algorithm.lower()}"
    
    try:
        # 获取当前模块中的函数
        embed_function = globals().get(function_name)
        if embed_function is None:
            raise ValueError(f"文本水印算法 {algorithm} 的实现函数 {function_name} 不存在")
        
        # 调用算法，获取处理后的文本内容
        processed_text = embed_function(input_file, watermark)
        
        # 文件保存逻辑
        original_name = os.path.basename(input_file)
        name_without_ext = os.path.splitext(original_name)[0]
        filename = f"{name_without_ext}_embed.txt"
        
        # 从app.config获取保存路径
        embed_dir = current_app.config['MEDIA_FOLDERS']['text']['embed']
        full_path = os.path.join(embed_dir, filename)
        
        # 保存文件
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(processed_text)
        
        return full_path  # 返回完整路径
        
    except Exception as e:
        print(f"文本水印算法 {algorithm} 失败: {str(e)}")
        raise

def extract(input_file, algorithm):
    """文本水印提取 - 支持多种算法（基于配置）"""
    # 直接生成函数名
    function_name = f"extract_{algorithm.lower()}"
    
    try:
        # 获取当前模块中的函数
        extract_function = globals().get(function_name)
        if extract_function is None:
            raise ValueError(f"文本水印算法 {algorithm} 的提取函数 {function_name} 不存在")
        
        return extract_function(input_file)
        
    except Exception as e:
        print(f"文本水印提取算法 {algorithm} 失败: {str(e)}")
        raise

def embed_lsb(input_file, watermark):
    print("text_watermark_embed!")
    return watermark

def extract_lsb(input_file):
    print("text_watermark_extract!")
    return "test"

def embed_dct(input_file, watermark):
    """DCT算法实现 - 后期实现"""
    raise NotImplementedError("文本DCT算法尚未实现")

def extract_dct(input_file):
    """DCT算法提取 - 后期实现"""
    raise NotImplementedError("文本DCT算法尚未实现") 
# Standard library imports
import os

# Third-party imports
from flask import current_app


def embed(input_file, watermark, algorithm):
    """文本水印嵌入 - 负责算法调用和文件保存"""
    
    # 获取文件扩展名
    _, extension = os.path.splitext(input_file)
    extension = extension[1:].lower()
    
    # 生成函数名 (格式: embed_扩展名_算法名)
    function_name = f"embed_{extension}_{algorithm.lower()}"
    
    try:
        # 获取当前模块中的函数
        embed_function = globals().get(function_name)
        if embed_function is None:
            raise ValueError(f"文本水印算法 {algorithm} 不支持 {extension} 格式")
        
        # 调用算法，获取处理后的文本内容
        processed_text = embed_function(input_file, watermark)
        
        # 文件保存逻辑
        original_name = os.path.basename(input_file)
        name_without_ext = os.path.splitext(original_name)[0]
        filename = f"{name_without_ext}_embed.{extension}"
        
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
    # 获取文件扩展名
    _, extension = os.path.splitext(input_file)
    extension = extension[1:].lower()
    
    # 生成函数名 (格式: extract_扩展名_算法名)
    function_name = f"extract_{extension}_{algorithm.lower()}"
    
    try:
        # 获取当前模块中的函数
        extract_function = globals().get(function_name)
        if extract_function is None:
            raise ValueError(f"文本水印算法 {algorithm} 不支持 {extension} 格式")
        
        return extract_function(input_file)
        
    except Exception as e:
        print(f"文本水印提取算法 {algorithm} 失败: {str(e)}")
        raise

# TXT格式的LSB实现
def embed_txt_lsb(input_file, watermark):
    """LSB算法实现 - TXT格式专用"""
    print("text_watermark_embed for TXT!")
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            file_content = file.read()
            # 这里可以添加水印处理逻辑
            return file_content  # 返回文件内容字符串
    except Exception as e:
        print(f"处理文件失败: {str(e)}")
        return None

def extract_txt_lsb(input_file):
    """LSB算法提取 - TXT格式专用"""
    print("text_watermark_extract for TXT!")
    return "test"

# PDF格式的LSB实现
def embed_pdf_lsb(input_file, watermark):
    """LSB算法实现 - PDF格式专用"""
    print("text_watermark_embed for PDF!")
    return watermark

def extract_pdf_lsb(input_file):
    """LSB算法提取 - PDF格式专用"""
    print("text_watermark_extract for PDF!")
    return "test"


# DCT算法实现
def embed_txt_dct(input_file, watermark):
    """DCT算法实现 - TXT格式专用"""
    raise NotImplementedError("TXT格式的DCT水印算法尚未实现")

def extract_txt_dct(input_file):
    """DCT算法提取 - TXT格式专用"""
    raise NotImplementedError("TXT格式的DCT水印提取算法尚未实现")

def embed_pdf_dct(input_file, watermark):
    """DCT算法实现 - PDF格式专用"""
    raise NotImplementedError("PDF格式的DCT水印算法尚未实现")

def extract_pdf_dct(input_file):
    """DCT算法提取 - PDF格式专用"""
    raise NotImplementedError("PDF格式的DCT水印提取算法尚未实现") 
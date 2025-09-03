# Standard library imports
import os

# Third-party imports
import numpy as np
from PIL import Image
from flask import current_app, flash

# 图像水印算法所需
import time
from blind_watermark import WaterMark, blind_watermark
blind_watermark.bw_notes.close()

WATERMARK_FIXED_LENGTH = 13  # 水印固定字符数（DCT专用）


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
        
        # 调用算法，获取处理后图像的保存路径
        full_path = embed_function(input_file, watermark)

        # 文件保存改到具体算法内
        # # 文件保存逻辑
        # original_name = os.path.basename(input_file)
        # name_without_ext = os.path.splitext(original_name)[0]
        # filename = f"{name_without_ext}_embed.{extension}"
        #
        # # 从app.config获取保存路径
        # embed_dir = current_app.config['MEDIA_FOLDERS']['image']['embed']
        # full_path = os.path.join(embed_dir, filename)
        #
        # # 保存文件
        # processed_image.save(full_path)
        
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

# # 具体算法实现 - BMP格式
# def embed_bmp_lsb(input_file, watermark):
#     """使用 LSB 算法在 BMP 图像中嵌入水印"""
#     # 打开图像
#     img = Image.open(input_file)
#     # 转换为 RGB 模式（如果不是的话）
#     if img.mode != 'RGB':
#         img = img.convert('RGB')
    
#     # 获取图像数据
#     pixels = np.array(img)
    
#     # 将水印文本转换为二进制
#     watermark_bits = ''.join(format(ord(c), '08b') for c in watermark)
#     watermark_length = len(watermark_bits)
    
#     # 检查图像容量是否足够
#     if watermark_length > pixels.size:
#         raise ValueError("水印太长，图像容量不足")
    
#     # 在图像的最低有效位嵌入水印
#     bit_index = 0
#     for i in range(pixels.shape[0]):
#         for j in range(pixels.shape[1]):
#             for k in range(pixels.shape[2]):
#                 if bit_index < watermark_length:
#                     # 修改最低有效位
#                     pixels[i, j, k] = (pixels[i, j, k] & ~1) | int(watermark_bits[bit_index])
#                     bit_index += 1
#                 else:
#                     break
#             if bit_index >= watermark_length:
#                 break
#         if bit_index >= watermark_length:
#             break
    
#     # 创建新图像
#     processed_image = Image.fromarray(pixels)
#     return processed_image

# # JPG格式的LSB实现
# def embed_jpg_lsb(input_file, watermark):
#     """使用 LSB 算法在 JPG 图像中嵌入水印"""
#     # 由于 JPG 的有损压缩特性，先将其转换为 BMP
#     img = Image.open(input_file)
#     return embed_bmp_lsb(img, watermark)

# # PNG格式的LSB实现
# def embed_png_lsb(input_file, watermark):
#     """使用 LSB 算法在 PNG 图像中嵌入水印"""
#     # PNG 可以直接使用 BMP 的实现
#     return embed_bmp_lsb(input_file, watermark)

# # 提取实现
# def extract_bmp_lsb(input_file):
#     return "test"
# def extract_jpg_lsb(input_file):
#     return "test"

# def extract_png_lsb(input_file):
#     return "test"

# DCT算法实现
def embed_jpg_dct(input_file, watermark):
    """DCT算法实现 - JPG格式专用"""
    # # 开始时间
    # start = time.time()

    # 验证水印长度
    if len(watermark) > (WATERMARK_FIXED_LENGTH - 3):
        flash(f"水印长度不能超过{WATERMARK_FIXED_LENGTH - 3}个字符", "error")
        return None
    else:
        # 需要补全的长度
        padding_len = WATERMARK_FIXED_LENGTH - len(watermark)
        middle_chars = padding_len - 2  # “印”的数量（减去开头和结尾的"水"）
        padding = "水" + "印" * middle_chars + "水"
        # 补全水印
        watermark = watermark + padding

    # 两个 password 决定嵌入方式，默认为 1，后续可用于拓展密钥或权限功能
    task = WaterMark(password_img=1, password_wm=1)
    task.read_img(input_file)
    task.read_wm(watermark, mode='str')

    # 文件保存逻辑
    original_name = os.path.basename(input_file)
    name_without_ext = os.path.splitext(original_name)[0]
    filename = f"{name_without_ext}_embed.{'jpg'}"

    # 从app.config获取保存路径
    embed_dir = current_app.config['MEDIA_FOLDERS']['image']['embed']
    full_path = os.path.join(embed_dir, filename)

    # 嵌入水印并保存文件
    task.embed(full_path)

    # # 计算嵌入时间
    # end = time.time()
    # embed_time = end - start

    return full_path

def embed_jpeg_dct(input_file, watermark):
    """DCT算法实现 - JPEG格式专用"""
    # # 开始时间
    # start = time.time()

    # 验证水印长度
    if len(watermark) > (WATERMARK_FIXED_LENGTH - 3):
        flash(f"水印长度不能超过{WATERMARK_FIXED_LENGTH - 3}个字符", "error")
        return None
    else:
        # 需要补全的长度
        padding_len = WATERMARK_FIXED_LENGTH - len(watermark)
        middle_chars = padding_len - 2  # “印”的数量（减去开头和结尾的"水"）
        padding = "水" + "印" * middle_chars + "水"
        # 补全水印
        watermark = watermark + padding

    # 两个 password 决定嵌入方式，默认为 1，后续可用于拓展密钥或权限功能
    task = WaterMark(password_img=1, password_wm=1)
    task.read_img(input_file)
    task.read_wm(watermark, mode='str')

    # 文件保存逻辑
    original_name = os.path.basename(input_file)
    name_without_ext = os.path.splitext(original_name)[0]
    filename = f"{name_without_ext}_embed.{'jpeg'}"

    # 从app.config获取保存路径
    embed_dir = current_app.config['MEDIA_FOLDERS']['image']['embed']
    full_path = os.path.join(embed_dir, filename)

    # 嵌入水印并保存文件
    task.embed(full_path)

    # # 计算嵌入时间
    # end = time.time()
    # embed_time = end - start

    return full_path

def embed_png_dct(input_file, watermark):
    """DCT算法实现 - PNG格式专用"""
    # # 开始时间
    # start = time.time()

    # 验证水印长度
    if len(watermark) > (WATERMARK_FIXED_LENGTH - 3):
        flash(f"水印长度不能超过{WATERMARK_FIXED_LENGTH - 3}个字符", "error")
        return None
    else:
        # 需要补全的长度
        padding_len = WATERMARK_FIXED_LENGTH - len(watermark)
        middle_chars = padding_len - 2  # “印”的数量（减去开头和结尾的"水"）
        padding = "水" + "印" * middle_chars + "水"
        # 补全水印
        watermark = watermark + padding

    # 两个 password 决定嵌入方式，默认为 1，后续可用于拓展密钥或权限功能
    task = WaterMark(password_img=1, password_wm=1)
    task.read_img(input_file)
    task.read_wm(watermark, mode='str')

    # 文件保存逻辑
    original_name = os.path.basename(input_file)
    name_without_ext = os.path.splitext(original_name)[0]
    filename = f"{name_without_ext}_embed.{'png'}"

    # 从app.config获取保存路径
    embed_dir = current_app.config['MEDIA_FOLDERS']['image']['embed']
    full_path = os.path.join(embed_dir, filename)

    # 嵌入水印并保存文件
    task.embed(full_path)

    # # 计算嵌入时间
    # end = time.time()
    # embed_time = end - start

    return full_path

def embed_bmp_dct(input_file, watermark):
    """DCT算法实现 - BMP格式专用"""
    # # 开始时间
    # start = time.time()

    # 验证水印长度
    if len(watermark) > (WATERMARK_FIXED_LENGTH - 3):
        flash(f"水印长度不能超过{WATERMARK_FIXED_LENGTH - 3}个字符", "error")
        return None
    else:
        # 需要补全的长度
        padding_len = WATERMARK_FIXED_LENGTH - len(watermark)
        middle_chars = padding_len - 2  # “印”的数量（减去开头和结尾的"水"）
        padding = "水" + "印" * middle_chars + "水"
        # 补全水印
        watermark = watermark + padding

    # 两个 password 决定嵌入方式，默认为 1，后续可用于拓展密钥或权限功能
    task = WaterMark(password_img=1, password_wm=1)
    task.read_img(input_file)
    task.read_wm(watermark, mode='str')

    # 文件保存逻辑
    original_name = os.path.basename(input_file)
    name_without_ext = os.path.splitext(original_name)[0]
    filename = f"{name_without_ext}_embed.{'bmp'}"

    # 从app.config获取保存路径
    embed_dir = current_app.config['MEDIA_FOLDERS']['image']['embed']
    full_path = os.path.join(embed_dir, filename)

    # 嵌入水印并保存文件
    task.embed(full_path)

    # # 计算嵌入时间
    # end = time.time()
    # embed_time = end - start

    return full_path

def extract_jpg_dct(input_file):
    """DCT算法提取 - JPG格式专用"""
    # # 开始时间
    # start = time.time()

    task = WaterMark(password_img=1, password_wm=1)
    watermark = task.extract(input_file, wm_shape=WATERMARK_FIXED_LENGTH * 24, mode='str')

    if len(watermark) != WATERMARK_FIXED_LENGTH:
        flash("提取失败：提取算法与原嵌入算法不匹配", "error")
        return None

    # 检查水印末尾是否符合padding模式
    if not watermark.endswith('水'):
        flash("提取失败：提取算法与原嵌入算法不匹配", "error")
        return None

    # 从末尾开始向前查找padding的开始位置
    # 找到第一个不是"印"的字符，这应该是padding的开头"水"
    i = len(watermark) - 2  # 从倒数第二个字符开始
    while i >= 0 and watermark[i] == '印':
        i -= 1

    # 如果找到了开头的"水"，并且这个"水"之后到末尾都是"印"和结尾的"水"
    if i >= 0 and watermark[i] == '水':
        # 去除padding部分
        original_watermark = watermark[:i]

        # # 计算嵌入时间
        # end = time.time()
        # embed_time = end - start

        return original_watermark

    # 如果不符合padding模式
    flash("提取失败：提取算法与原嵌入算法不匹配", "error")
    return None

def extract_jpeg_dct(input_file):
    """DCT算法提取 - JPEG格式专用"""
    # # 开始时间
    # start = time.time()

    task = WaterMark(password_img=1, password_wm=1)
    watermark = task.extract(input_file, wm_shape=WATERMARK_FIXED_LENGTH * 24, mode='str')

    if len(watermark) != WATERMARK_FIXED_LENGTH:
        flash("提取失败：提取算法与原嵌入算法不匹配", "error")
        return None

    # 检查水印末尾是否符合padding模式
    if not watermark.endswith('水'):
        flash("提取失败：提取算法与原嵌入算法不匹配", "error")
        return None

    # 从末尾开始向前查找padding的开始位置
    # 找到第一个不是"印"的字符，这应该是padding的开头"水"
    i = len(watermark) - 2  # 从倒数第二个字符开始
    while i >= 0 and watermark[i] == '印':
        i -= 1

    # 如果找到了开头的"水"，并且这个"水"之后到末尾都是"印"和结尾的"水"
    if i >= 0 and watermark[i] == '水':
        # 去除padding部分
        original_watermark = watermark[:i]

        # # 计算嵌入时间
        # end = time.time()
        # embed_time = end - start

        return original_watermark

    # 如果不符合padding模式
    flash("提取失败：提取算法与原嵌入算法不匹配", "error")
    return None

def extract_png_dct(input_file):
    """DCT算法提取 - PNG格式专用"""
    # # 开始时间
    # start = time.time()

    task = WaterMark(password_img=1, password_wm=1)
    watermark = task.extract(input_file, wm_shape=WATERMARK_FIXED_LENGTH * 24, mode='str')

    if len(watermark) != WATERMARK_FIXED_LENGTH:
        flash("提取失败：提取算法与原嵌入算法不匹配", "error")
        return None

    # 检查水印末尾是否符合padding模式
    if not watermark.endswith('水'):
        flash("提取失败：提取算法与原嵌入算法不匹配", "error")
        return None

    # 从末尾开始向前查找padding的开始位置
    # 找到第一个不是"印"的字符，这应该是padding的开头"水"
    i = len(watermark) - 2  # 从倒数第二个字符开始
    while i >= 0 and watermark[i] == '印':
        i -= 1

    # 如果找到了开头的"水"，并且这个"水"之后到末尾都是"印"和结尾的"水"
    if i >= 0 and watermark[i] == '水':
        # 去除padding部分
        original_watermark = watermark[:i]

        # # 计算嵌入时间
        # end = time.time()
        # embed_time = end - start

        return original_watermark

    # 如果不符合padding模式
    flash("提取失败：提取算法与原嵌入算法不匹配", "error")
    return None

def extract_bmp_dct(input_file):
    """DCT算法提取 - BMP格式专用"""
    # # 开始时间
    # start = time.time()

    task = WaterMark(password_img=1, password_wm=1)
    watermark = task.extract(input_file, wm_shape=WATERMARK_FIXED_LENGTH * 24, mode='str')

    if len(watermark) != WATERMARK_FIXED_LENGTH:
        flash("提取失败：提取算法与原嵌入算法不匹配", "error")
        return None

    # 检查水印末尾是否符合padding模式
    if not watermark.endswith('水'):
        flash("提取失败：提取算法与原嵌入算法不匹配", "error")
        return None

    # 从末尾开始向前查找padding的开始位置
    # 找到第一个不是"印"的字符，这应该是padding的开头"水"
    i = len(watermark) - 2  # 从倒数第二个字符开始
    while i >= 0 and watermark[i] == '印':
        i -= 1

    # 如果找到了开头的"水"，并且这个"水"之后到末尾都是"印"和结尾的"水"
    if i >= 0 and watermark[i] == '水':
        # 去除padding部分
        original_watermark = watermark[:i]

        # # 计算嵌入时间
        # end = time.time()
        # embed_time = end - start

        return original_watermark

    # 如果不符合padding模式
    flash("提取失败：提取算法与原嵌入算法不匹配", "error")
    return None

# # Cox算法实现
# def embed_jpg_cox(input_file, watermark):
#     """Cox算法实现 - JPG格式专用"""
#     raise NotImplementedError("JPG格式的Cox水印算法尚未实现")

# def extract_jpg_cox(input_file):
#     """Cox算法提取 - JPG格式专用"""
#     raise NotImplementedError("JPG格式的Cox水印提取算法尚未实现")

# def embed_bmp_cox(input_file, watermark):
#     """Cox算法实现 - BMP格式专用"""
#     raise NotImplementedError("BMP格式的Cox水印算法尚未实现")

# def extract_bmp_cox(input_file):
#     """Cox算法提取 - BMP格式专用"""
#     raise NotImplementedError("BMP格式的Cox水印提取算法尚未实现")

# # DWT算法实现
# def embed_jpg_dwt(input_file, watermark):
#     """DWT算法实现 - JPG格式专用"""
#     raise NotImplementedError("JPG格式的DWT水印算法尚未实现")

# def extract_jpg_dwt(input_file):
#     """DWT算法提取 - JPG格式专用"""
#     raise NotImplementedError("JPG格式的DWT水印提取算法尚未实现")

# def embed_bmp_dwt(input_file, watermark):
#     """DWT算法实现 - BMP格式专用"""
#     raise NotImplementedError("BMP格式的DWT水印算法尚未实现")

# def extract_bmp_dwt(input_file):
#     """DWT算法提取 - BMP格式专用"""
#     raise NotImplementedError("BMP格式的DWT水印提取算法尚未实现")
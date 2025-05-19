from PIL import Image
from numpy import *
import os
embed_dir=upload_dir=os.path.join(os.getcwd(),'embed_file')

# 嵌入水印
def bin_value(value, bitsize):  # 将整数转化为固定长度的二进制字符串
    binval = bin(value)[2:]
    if len(binval) > bitsize:
        print("Too Large!")
    while len(binval) < bitsize:
        binval = "0" + binval
    return binval


def embed(input, watermark):
    print("image_watermark_embed!")
    im = Image.open(input)
    im = im.convert('L')  # 转化为灰度图片
    file_name = input.split("\\")[-1]+'.bmp'
    im.save(file_name)  # 防止压缩时水印易被破坏，bmp没有任何与圧缩过程

    im = Image.open(file_name)

    im_array = array(im)  # 转化为数组
    row, col = im_array.shape
    im_array_flatten = im_array.flatten()  # 转化为一位数组

    # 将水印字符串转换为UTF-8编码的字节
    data_bytes = watermark.encode('utf-8')
    # 存储字节数而不是字符数
    data_length = len(data_bytes)
    
    # 检查图像容量是否足够
    if row * col < 8 + data_length * 8:
        raise ValueError(f"图像容量不足，无法嵌入长度为{data_length}字节的水印")
        
    bindata = bin_value(data_length, 32)  # 使用32位来存储长度，支持更长的水印

    index = 0  #
    for c in bindata:  # 把长度嵌入
        if int(c) == 0:
            im_array_flatten[index] = im_array_flatten[index] & 254
        else:
            im_array_flatten[index] = im_array_flatten[index] | 1
        index += 1

    for byte in data_bytes:  # 把内容嵌入（处理字节而不是字符）
        for c in bin_value(byte, 8):
            if int(c) == 0:
                im_array_flatten[index] = im_array_flatten[index] & 254
            else:
                im_array_flatten[index] = im_array_flatten[index] | 1
            index += 1

    image_array_embed = reshape(im_array_flatten, (row, col))  # 一维转化为二维数组
    im_embed = Image.fromarray(image_array_embed)
    file_name = input.split("\\")[-1]+"_embed.bmp"
    im_embed.save(os.path.join(embed_dir,file_name))
    # os.remove(file_name)

    # 水印提取


def extract(input):
    print("image_watermark_extract!")
    im = Image.open(input)
    im_array = array(im)  # 转化为数组
    im_array_flatten = im_array.flatten()  # 转化为一位数组
    
    # 提取水印长度（32位）
    str_length = ''
    index = 0
    while index < 32:  # 提取长度（修改为32位）
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
        # 解码失败时尝试其他编码或返回错误信息
        result = "水印解码失败，可能是损坏的数据"

    print(result)
    return result

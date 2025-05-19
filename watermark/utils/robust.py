import cv2
import numpy as np
# 不同图片选择的像素点不同（白色背景 or 风景图片）


def bin_value(value, bitsize=8):
    binval = bin(value)[2:]
    if len(binval) > bitsize:
        print("Larger than the expected size")
    while len(binval) < bitsize:
        binval = "0" + binval
    return binval

# 扩频
def spread_spectrum(bit_string, spread_width):
    ret = ""
    for bit in bit_string:#字符串串接
        ret += bit * spread_width
    return ret


def get_original_bin(bit_string, spread_width):
    if len(bit_string) % spread_width != 0:#看扩频后是否为整数倍
        print("长度错误，需是%d整数倍。" % spread_width)
        return None

    ret_string = ""
    for i in range(int(len(bit_string) / spread_width)):#每一组统计1的个数
        count = 0
        for j in range(spread_width):
            count += int(bit_string[i * spread_width + j])
        if count < spread_width /3:# 阈值为50%，1的个数没超过50%
            ret_string += "0"
        elif count > spread_width-spread_width /3:
            ret_string += "1"#0的个数没超过50%

    return ret_string


def watermark_encode(watermark_string):
    # 初始化水印信息
    watermark = ""

    # 将水印字符串转换为UTF-8编码的字节
    watermark_bytes = watermark_string.encode('utf-8')
    
    # 水印字节长度转化为32bits的二进制字符串并加入水印信息中
    watermark_size = bin_value(len(watermark_bytes), 16)  # 用16位存储长度，支持更长的UTF-8文本
    watermark += spread_spectrum(watermark_size, 7)

    # 循环转化字节为二进制字符串并加入水印信息中
    for byte in watermark_bytes:
        temp_string = bin_value(byte)
        watermark += spread_spectrum(temp_string, 7)
    return watermark

# 水印强度
def embed_bit(bit, dcted_block, alpha):
    if bit == 1:
        if dcted_block[4, 3] < dcted_block[5, 2]:
            # 使用临时变量进行交换，避免numpy视图引用问题
            temp = dcted_block[4, 3].copy()
            dcted_block[4, 3] = dcted_block[5, 2].copy()
            dcted_block[5, 2] = temp
            if dcted_block[4, 3] - dcted_block[5, 2] < alpha:
                dcted_block[4, 3] += alpha
        elif dcted_block[4, 3] == dcted_block[5, 2]:
            dcted_block[4, 3] += alpha
    elif bit == 0:
        if dcted_block[4, 3] > dcted_block[5, 2]:
            # 使用临时变量进行交换，避免numpy视图引用问题
            temp = dcted_block[4, 3].copy()
            dcted_block[4, 3] = dcted_block[5, 2].copy()
            dcted_block[5, 2] = temp
            if dcted_block[5, 2] - dcted_block[4, 3] < alpha:
                dcted_block[4, 3] -= alpha
        elif dcted_block[4, 3] == dcted_block[5, 2]:
            dcted_block[4, 3] -= alpha
    else:
        print("请输入正确的水印值，0或1。")


def extract_bit(dcted_block):
    if dcted_block[4, 3] > dcted_block[5, 2]:
        return 1
    else:
        return 0


def embed_watermark(image, watermark_string):
    # 确保图像存在且维度正确
    if image is None or image.size == 0:
        print("无效的图像数据")
        return False

    # 打印尺寸信息，以便调试
    iHeight, iWidth = image.shape
    print(f"水印嵌入 - 图像尺寸: {iWidth}x{iHeight}")
    
    # 检查图像尺寸是否为8的倍数，DCT需要
    if iHeight % 8 != 0 or iWidth % 8 != 0:
        print(f"警告：图像尺寸不是8的倍数: {iWidth}x{iHeight}，可能影响DCT处理")
    
    # 确保图像数据类型兼容
    if not np.issubdtype(image.dtype, np.integer):
        print(f"转换图像数据类型从 {image.dtype} 到 uint8")
        image = image.astype(np.uint8)
    
    # 获取水印编码
    watermark = watermark_encode(watermark_string)
    
    # 检查水印长度是否超过可用空间
    blocks_needed = len(watermark)
    blocks_available = (iHeight // 8) * (iWidth // 8)
    if blocks_needed > blocks_available:
        print(f"警告：水印需要{blocks_needed}个块，但只有{blocks_available}个可用块")
    
    # 初始化空矩阵保存量化结果
    img2 = np.empty(shape=(iHeight, iWidth))

    index = 0

    # 分块DCT
    for startY in range(0, iHeight, 8):
        if startY + 8 > iHeight:
            break
            
        for startX in range(0, iWidth, 8):
            if startX + 8 > iWidth:
                break
                
            block = image[startY:startY + 8, startX:startX + 8].reshape((8, 8))

            # 进行DCT
            blockf = np.float32(block)
            block_dct = cv2.dct(blockf)

            if index < len(watermark):
                embed_bit(int(watermark[index]), block_dct, 50)
                index += 1

            # store the result
            for y in range(8):
                for x in range(8):
                    img2[startY + y, startX + x] = block_dct[y, x]


    # DCT逆变换
    for startY in range(0, iHeight, 8):
        if startY + 8 > iHeight:
            break
            
        for startX in range(0, iWidth, 8):
            if startX + 8 > iWidth:
                break
                
            block = img2[startY:startY + 8, startX:startX + 8].reshape((8, 8))

            blockf = np.float32(block)
            dst = cv2.idct(blockf)

            # 保存逆变换结果
            for y in range(8):
                for x in range(8):
                    image[startY + y, startX + x] = dst[y, x]
    
    return True



def extract_watermark(image):
    # 确保图像存在且维度正确
    if image is None or image.size == 0:
        print("无效的图像数据")
        return "无效的图像数据"

    # 打印尺寸信息，以便调试
    iHeight, iWidth = image.shape
    print(f"水印提取 - 图像尺寸: {iWidth}x{iHeight}")
    
    # 检查图像尺寸是否为8的倍数
    if iHeight % 8 != 0 or iWidth % 8 != 0:
        print(f"警告：图像尺寸不是8的倍数: {iWidth}x{iHeight}，可能影响DCT处理")

    # 确保图像数据类型兼容
    if not np.issubdtype(image.dtype, np.integer):
        print(f"转换图像数据类型从 {image.dtype} 到 uint8")
        image = image.astype(np.uint8)

    index = 0
    length_string = ""
    watermark_length = 0
    watermark_string = ""

    # 分块DCT
    for startY in range(0, iHeight, 8):
        if startY + 8 > iHeight:
            break
            
        for startX in range(0, iWidth, 8):
            if startX + 8 > iWidth:
                break
                
            block = image[startY:startY + 8, startX:startX + 8].reshape((8, 8))

            # 进行DCT
            blockf = np.float32(block)
            block_dct = cv2.dct(blockf)

            if index < 16 * 7:  # 读取16位长度信息
                bit = extract_bit(block_dct)

                if bit == 1:
                    length_string += "1"
                else:
                   length_string += "0"

                if index == 16 * 7 - 1:
                    length_string = get_original_bin(length_string, 7)
                    try:
                        watermark_length = int(length_string, 2)
                        print(f"检测到水印长度: {watermark_length} 字节")
                    except ValueError:
                        print("水印长度解码失败")
                        return "水印解码失败"

                index += 1

            elif index < 16 * 7 + watermark_length * 8 * 7:
                bit = extract_bit(block_dct)

                if bit == 1:
                    watermark_string += "1"
                else:
                    watermark_string += "0"

                if index == 16 * 7 + watermark_length * 8 * 7 - 1:
                    watermark_string = get_original_bin(watermark_string, 7)
                    
                    # 收集所有字节
                    try:
                        bytes_data = bytearray()
                        for i in range(watermark_length):
                            byte_value = int(watermark_string[i*8 : (i+1)*8], 2)
                            bytes_data.append(byte_value)
                        
                        # 将字节转换回UTF-8字符串
                        try:
                            decoded_watermark = bytes_data.decode('utf-8')
                        except UnicodeDecodeError:
                            decoded_watermark = "水印解码失败，可能是损坏的数据"
                        
                        return decoded_watermark
                    except Exception as e:
                        print(f"处理水印字节时出错: {str(e)}")
                        return f"水印解码失败: {str(e)}"

                index += 1
    
    return "未找到水印或水印不完整"
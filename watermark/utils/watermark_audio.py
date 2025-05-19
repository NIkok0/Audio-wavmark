import wave
import struct
import os
embed_dir=os.path.join(os.getcwd(),'embed_file')

def bin_value(value, bitsize=8):
    binval = bin(value)[2:]
    # bin是把十进制数转化为二进制形式的字符串，前面有个0b表示二进制，所以要去掉
    if len(binval) > bitsize:
        print("Larger than the expected size")
    while len(binval) < bitsize:
        binval = "0" + binval
        # 循环在字符串前面拼接0，直到字符串长度为bitsize
    return binval

def embed(input, watermark_str):
    print("audio_watermark_embed:")
    try:
        # 确保输出目录存在
        if not os.path.exists(embed_dir):
            os.makedirs(embed_dir)
            
        # 正确处理文件名，使用os.path代替手动分割
        input_basename = os.path.basename(input)
        output_filename = f"{input_basename}_embed.wav"
        output_path = os.path.join(embed_dir, output_filename)
        
        print(f"输入音频: {input}")
        print(f"输出路径: {output_path}")
        
        # 初始化水印信息
        watermark = ""
        
        # 将水印字符串转换为UTF-8编码的字节
        watermark_bytes = watermark_str.encode('utf-8')
        
        # 水印字节长度转化为32bits的二进制字符串并加入水印信息中
        watermark_size = bin_value(len(watermark_bytes), 32)
        watermark += watermark_size
        
        # 循环转化字节为二进制字符串并加入水印信息中
        for byte in watermark_bytes:
            watermark += bin_value(byte)
            
        # 利用wave库读取wav文件
        cover_audio = wave.open(input, 'rb')
        # 保存wav原始文件的参数信息
        (nchannels, sampwidth, framerate, nframes, comptype, compname) = cover_audio.getparams()
        # 读取所有数据，数据长度为帧数*声道数
        frames = cover_audio.readframes(nframes * nchannels)
        #解析帧数据
        samples = struct.unpack_from("%dh" % nframes * nchannels, frames)
        # 水印过长时抛出异常
        if len(samples) < len(watermark):
            raise OverflowError(
                "水印长度共%d比特，采样点数量为%d，采样点不足请减少水印长度。" % (
                    len(watermark), len(samples)))
        encoded_samples = []
        watermark_position = 0
        for sample in samples:
            encoded_sample = sample
            if watermark_position < len(watermark):
                encode_bit = int(watermark[watermark_position])
                if encode_bit == 1:
                    encoded_sample = sample | 1
                else:
                    encoded_sample = sample
                    if sample & 1 != 0:
                        encoded_sample = sample - 1
                watermark_position = watermark_position + 1
            encoded_samples.append(encoded_sample)
            
        # 写入文件
        encoded_audio = wave.open(output_path, 'wb')
        encoded_audio.setparams((nchannels, sampwidth, framerate, nframes, comptype, compname))
        encoded_frames = struct.pack("%dh" % len(encoded_samples), *encoded_samples)
        encoded_audio.writeframes(encoded_frames)
        encoded_audio.close()
        cover_audio.close()
        
        # 验证文件是否成功生成
        if os.path.exists(output_path):
            print(f"音频水印添加成功: {output_path}")
            return output_path
        else:
            print(f"音频水印添加失败: {output_path}")
            return None
            
    except Exception as e:
        print(f"音频水印添加出错: {str(e)}")
        return None


def extract(input):
    print("audio_watermark_extract!")
    try:
        watermarked_audio = wave.open(input, 'rb')
        (nchannels, sampwidth, framerate, nframes, comptype, compname) = watermarked_audio.getparams()
        frames = watermarked_audio.readframes(nframes * nchannels)
        samples = struct.unpack_from("%dh" % nframes * nchannels, frames)
        
        # 提取水印字节数量（前32位）
        watermark_bytes = ""
        for i in range(32):
            if samples[i] & 1 == 0:
                watermark_bytes += '0'
            else:
                watermark_bytes += '1'
        watermark_size = int(watermark_bytes, 2)
        print("提取到长度为%d字节的水印。" % watermark_size)
        
        # 提取水印字节
        bytes_data = bytearray()
        sample_index = 32
        for n in range(watermark_size):
            byte_bits = ""
            for i in range(8):
                if samples[sample_index] & 1 == 0:
                    byte_bits += '0'
                else:
                    byte_bits += '1'
                sample_index += 1
            bytes_data.append(int(byte_bits, 2))
        
        # 将字节转换回UTF-8字符串
        try:
            watermark = bytes_data.decode('utf-8')
        except UnicodeDecodeError:
            watermark = "水印解码失败，可能是损坏的数据"
            
        watermarked_audio.close()
        print(watermark)
        return watermark
        
    except Exception as e:
        print(f"音频水印提取出错: {str(e)}")
        return "水印提取失败: " + str(e)


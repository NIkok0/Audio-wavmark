FFMPEG_BIN = "ffmpeg.exe"

import subprocess as sp#调用外部程序
import numpy
import watermark.utils.robust as robust
import os
import json

#embed_dir
embed_dir=os.path.join(os.getcwd(),'embed_file')

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

def embed(input_video, watermark_string):
    print("video_watermark_embed!")
    
    # 确保embed_dir目录存在
    if not os.path.exists(embed_dir):
        os.makedirs(embed_dir)
    
    # 正确处理文件名，使用os.path代替手动分割
    input_basename = os.path.basename(input_video)
    output_filename = f"{input_basename}_embed.mp4"  # 改用更通用的mp4格式
    output_path = os.path.join(embed_dir, output_filename)
    
    print(f"输入视频: {input_video}")
    print(f"输出路径: {output_path}")

    # 检查输入文件是否存在且可读
    if not os.path.exists(input_video):
        print(f"错误: 输入视频文件不存在: {input_video}")
        return None
        
    # 获取视频分辨率和像素格式
    try:
        width, height, pix_fmt = get_video_info(input_video)
        print(f"视频分辨率: {width}x{height}, 像素格式: {pix_fmt}")
    except Exception as e:
        print(f"读取视频信息失败，使用默认参数: {str(e)}")
        width, height, pix_fmt = 1920, 1080, 'yuv420p'

    # 计算每帧大小
    frame_size = width * height * 3  # 假设3通道YUV
    
    # 使用两阶段处理 - 直接用ffmpeg生成中间可处理格式
    temp_yuv_file = os.path.join(embed_dir, f"temp_{os.path.splitext(input_basename)[0]}.yuv")
    
    # 1. 转换为原始YUV格式，便于处理
    try:
        convert_cmd = [
            FFMPEG_BIN,
            '-y',
            '-i', input_video,
            '-f', 'rawvideo',
            '-pix_fmt', 'yuv420p',
            '-s', f'{width}x{height}',
            temp_yuv_file
        ]
        
        print("执行视频转换命令...")
        convert_process = sp.run(convert_cmd, stdout=sp.PIPE, stderr=sp.PIPE)
        
        if convert_process.returncode != 0:
            print(f"视频转换失败，错误信息: {convert_process.stderr.decode('utf-8', errors='ignore')}")
            return None
            
        if not os.path.exists(temp_yuv_file) or os.path.getsize(temp_yuv_file) == 0:
            print(f"临时YUV文件创建失败: {temp_yuv_file}")
            return None
            
        print(f"视频转换成功，临时文件: {temp_yuv_file}")
    except Exception as e:
        print(f"视频转换过程出错: {str(e)}")
        return None
    
    # 2. 读取YUV文件并处理
    try:
        with open(temp_yuv_file, 'rb') as f:
            raw_data = f.read(frame_size)
            if not raw_data or len(raw_data) < frame_size:
                print(f"YUV文件读取失败，期望大小: {frame_size}，实际读取: {len(raw_data) if raw_data else 0}")
                return None
                
            # 处理第一帧
            image = numpy.frombuffer(raw_data, dtype='uint8')
            image = image.reshape((height, width, 3))
            
            # 获取Y通道
            img_tmp = image[:height, :width, 0].copy()  # 确保是副本
            
            # 嵌入水印
            print(f"开始嵌入水印: '{watermark_string}'")
            success = robust.embed_watermark(img_tmp, watermark_string)
            if not success:
                print("水印嵌入失败")
                return None
                
            # 更新Y通道
            image[:height, :width, 0] = img_tmp
            
            # 保存处理后的YUV
            processed_yuv = os.path.join(embed_dir, f"processed_{os.path.splitext(input_basename)[0]}.yuv")
            with open(processed_yuv, 'wb') as out_f:
                out_f.write(image.tobytes())
                # 写入剩余帧（不做处理）
                remaining_data = f.read()
                if remaining_data:
                    out_f.write(remaining_data)
    except Exception as e:
        print(f"处理YUV数据时出错: {str(e)}")
        if os.path.exists(temp_yuv_file):
            try:
                os.remove(temp_yuv_file)
            except:
                pass
        return None
    
    # 3. 转换回视频格式
    try:
        encode_cmd = [
            FFMPEG_BIN,
            '-y',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-s', f'{width}x{height}',
            '-pix_fmt', 'yuv420p',
            '-i', processed_yuv,
            '-c:v', 'libx264',  # 使用H.264编码，兼容性更好
            '-preset', 'medium',
            '-crf', '23',
            output_path
        ]
        
        print("执行视频编码命令...")
        encode_process = sp.run(encode_cmd, stdout=sp.PIPE, stderr=sp.PIPE)
        
        if encode_process.returncode != 0:
            print(f"视频编码失败，错误信息: {encode_process.stderr.decode('utf-8', errors='ignore')}")
            return None
    except Exception as e:
        print(f"视频编码过程出错: {str(e)}")
        return None
    finally:
        # 清理临时文件
        for temp_file in [temp_yuv_file, processed_yuv]:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
    
    # 验证文件是否成功生成
    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:  # 确保文件大小合理
        print(f"视频水印添加成功: {output_path}, 大小: {os.path.getsize(output_path)} 字节")
        return output_path
    else:
        print(f"视频水印添加失败: {output_path}, {'文件不存在' if not os.path.exists(output_path) else f'文件大小异常: {os.path.getsize(output_path)} 字节'}")
        return None


def extract(input_video):
    print("video_watermark_extract!")
    
    # 获取视频分辨率和像素格式
    try:
        width, height, pix_fmt = get_video_info(input_video)
        print(f"提取水印 - 视频分辨率: {width}x{height}, 像素格式: {pix_fmt}")
    except Exception as e:
        print(f"读取视频信息失败，使用默认参数: {str(e)}")
        width, height, pix_fmt = 1920, 1080, 'yuv420p'

    # 计算每帧大小
    frame_size = width * height * 3  # 假设3通道YUV
    
    command_read = [FFMPEG_BIN,
                    '-i', input_video,
                    '-f', 'image2pipe',
                    '-pix_fmt', pix_fmt,
                    '-vcodec', 'rawvideo', '-']
    pipe_read = sp.Popen(command_read, stdout=sp.PIPE, bufsize=10 ** 8)

    raw_image = pipe_read.stdout.read(frame_size)
    result = []
    
    try:
        while raw_image != None and len(raw_image) != 0:
            # transform the byte read into a numpy array
            image = numpy.frombuffer(raw_image, dtype='uint8')
            image = image.reshape((height, width, 3))
            # throw away the data in the pipe's buffer.
            pipe_read.stdout.flush()

            img_tmp = image[:height, :width, 0]
            result.append(robust.extract_watermark(img_tmp))
            raw_image = pipe_read.stdout.read(frame_size)
            break  # 只提取第一帧的水印
    except Exception as e:
        print(f"提取视频水印时出错: {str(e)}")
        if pipe_read and pipe_read.stdout:
            pipe_read.stdout.close()
        return f"提取水印失败: {str(e)}"
        
    if result and len(result) > 0:
        return result[0]
    else:
        return "未能提取水印"






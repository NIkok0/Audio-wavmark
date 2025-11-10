# Standard library imports
import json
import subprocess as sp
import numpy as np
import wave
from flask import current_app
import hashlib

# Third-party imports
from watermark.utils.path_utils import get_user_dated_embed_dir

import os
import ffmpeg
import numpy as np
import subprocess
import torch
import tqdm

from . import videoseal
from .videoseal.models import Videoseal
from .videoseal.evals.metrics import bit_accuracy

def text_to_6char_hash(text,random_seed):
    """
    将任意长度的文本转换为6位字符的hash值
    使用随机数种子拼接后进行SHA256 hash，然后截取前6位
    
    Args:
        text (str): 输入的任意文本
        
    Returns:
        str: 6位字符的hash值
    """
    # 生成随机数种子（8位数字）
    
    
    # 将文本与随机数种子拼接
    text_with_seed = f"{text}{random_seed}"
    
    # 使用SHA256算法生成hash
    hash_obj = hashlib.sha256(text_with_seed.encode('utf-8'))
    hash_hex = hash_obj.hexdigest()
    
    # 截取前6位字符并转换为大写
    result_hash = hash_hex[:6].upper()
    
    print(f"随机种子: {random_seed}")
    print(f"拼接后文本: {text_with_seed}")
    print(f"SHA256 hash (前6位): {result_hash}")
    
    return result_hash


def embed(input_file, watermark, algorithm, random_seed=None):
    """视频水印嵌入 - 负责算法调用和文件保存（兼容老版本行为）

    - 未提供 random_seed：内部生成 8 位数字种子，仅返回处理后文件路径。
    - 提供了 random_seed：返回 (full_path, watermark_hash)。
    """
    import secrets

    # 判断是否外部显式提供了种子
    provided_seed = random_seed is not None

    # 未提供则内部生成 8 位数字种子
    if random_seed is None:
        random_seed = str(secrets.randbelow(10**8)).zfill(8)

    # 将输入的水印文本转换为6位hash值
    watermark_hash = text_to_6char_hash(watermark, random_seed)
    print(f"原始水印文本: {watermark}")
    print(f"转换后的6位hash: {watermark_hash}")
    
    # 获取文件扩展名
    _, extension = os.path.splitext(input_file)
    extension = extension[1:].lower()
    
    # 生成函数名 (格式: embed_扩展名_算法名)
    function_name = f"embed_{extension}_{algorithm.lower()}"
    
    try:
        # 获取当前模块中的函数
        embed_function = globals().get(function_name)
        if embed_function is None:
            raise ValueError(f"视频水印算法 {algorithm} 不支持 {extension} 格式")
        
        # 调用算法，使用转换后的hash值
        processed_video = embed_function(input_file, watermark_hash)
        
        
        # 文件保存逻辑
        original_name = os.path.basename(input_file)
        name_without_ext = os.path.splitext(original_name)[0]
        filename = f"{name_without_ext}_embed.{extension}"
        
        # 从app.config获取保存路径 - 使用用户日期分层路径
        embed_dir = get_user_dated_embed_dir('video')
        full_path = os.path.join(embed_dir, filename)
        
        # 保存文件 - 在这种情况下，processed_video已经是保存好的文件路径
        # 因为视频处理过程中需要直接写入文件
        if os.path.exists(processed_video) and processed_video != full_path:
            os.rename(processed_video, full_path)
        
        # 返回：与旧版兼容
        if provided_seed:
            return full_path, watermark_hash
        return full_path
        
    except Exception as e:
        print(f"视频水印算法 {algorithm} 失败: {str(e)}")
        raise

def extract(input_file, algorithm):
    """视频水印提取 - 支持多种算法（基于配置）"""
    # 获取文件扩展名
    _, extension = os.path.splitext(input_file)
    extension = extension[1:].lower()
    
    # 生成函数名 (格式: extract_扩展名_算法名)
    function_name = f"extract_{extension}_{algorithm.lower()}"
    
    try:
        # 获取当前模块中的函数
        extract_function = globals().get(function_name)
        if extract_function is None:
            raise ValueError(f"视频水印算法 {algorithm} 不支持 {extension} 格式")
        
        return extract_function(input_file)
        
    except Exception as e:
        print(f"视频水印提取算法 {algorithm} 失败: {str(e)}")
        raise

# MP4格式的DCT实现
def embed_mp4_dct(input_file, watermark):
    """DCT算法实现 - MP4格式专用"""
    print("video_watermark_embed for MP4!")
    class Args:
        input = input_file
        output = get_user_dated_embed_dir('video')

    args = Args()
    os.makedirs(args.output, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    video_model = videoseal.load("videoseal")
    video_model.eval()
    video_model.to(device)
    video_model.compile()
    # current_dir = os.getcwd()
    # 文件保存逻辑
    original_name = os.path.basename(args.input)
    name_without_ext = os.path.splitext(original_name)[0]
    # filename = f"{name_without_ext}_embed.{'png'}"
    filename = f"{name_without_ext}_embed.{'mp4'}"
    full_path = os.path.join(args.output, filename)
    # output = os.path.join(current_dir, args.output)
    msgs_ori = embed_video(video_model, args.input, args.output, 16, watermark, full_path)

        
    return full_path  # 返回完整路径

# MP4格式的DCT实现
def embed_avi_dct(input_file, watermark):
    """DCT算法实现 - AVI格式专用"""
    print("video_watermark_embed for AVI!")
    class Args:
        input = input_file
        output = get_user_dated_embed_dir('video')

    args = Args()
    os.makedirs(args.output, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    video_model = videoseal.load("videoseal")
    video_model.eval()
    video_model.to(device)
    video_model.compile()
    current_dir = os.getcwd()
    # 文件保存逻辑
    original_name = os.path.basename(args.input)
    name_without_ext = os.path.splitext(original_name)[0]
    # filename = f"{name_without_ext}_embed.{'png'}"
    filename = f"{name_without_ext}_embed.{'avi'}"

    full_path = os.path.join(args.output, filename)
    msgs_ori = embed_video(video_model, args.input, args.output, 16, watermark, full_path)

        
    return full_path  # 返回完整路径

def bit_tensor_to_string(bits: torch.Tensor, max_chars: int = 32) -> str:
    bits = bits.squeeze()
    bits = torch.round(bits).clamp(0, 1).int().tolist()  # Ensure only 0 or 1
    chars = []
    for i in range(0, min(len(bits), max_chars * 8), 8):
        byte = bits[i:i + 8]
        if len(byte) < 8:
            break  # Not enough bits for a full character
        byte_str = ''.join(map(str, byte))
        char_code = int(byte_str, 2)
        # 只保留可打印的ASCII字符，跳过null字符和控制字符
        if char_code >= 32 and char_code <= 126:  # 可打印ASCII范围
            chars.append(chr(char_code))
        elif char_code == 0:  # 遇到null字符时停止
            break
    return ''.join(chars)


def string_to_bit_tensor(msg: str, target_length: int = 256) -> torch.Tensor:
    """
    Converts a string to a 1D bit tensor of shape (1, target_length).
    Pads with zeros if string is too short.
    """
    bits = ''.join(f'{ord(c):08b}' for c in msg)  # Convert each char to 8 bits
    bits = bits[:target_length]                  # Truncate if longer than 256 bits
    bits += '0' * (target_length - len(bits))    # Pad with zeros
    bit_list = [int(b) for b in bits]
    return torch.tensor([bit_list], dtype=torch.float32)  # Shape: (1, 256)

def embed_video_clip(
    model: Videoseal, clip: np.ndarray, msgs: torch.Tensor
) -> np.ndarray:
    clip_tensor = torch.tensor(clip, dtype=torch.float32).permute(0, 3, 1, 2) / 255.0
    outputs = model.embed(
        clip_tensor, msgs=msgs, is_video=True, lowres_attenuation=True
    )
    processed_clip = outputs["imgs_w"]
    processed_clip = (processed_clip * 255.0).byte().permute(0, 2, 3, 1).numpy()
    return processed_clip


def embed_video(
    model: Videoseal, input_path: str, output_path: str, chunk_size: int, watermark: str, full_path: str, crf: int = 23
) -> None:
    
    # Read video dimensions
    probe = ffmpeg.probe(input_path)
    
    video_info = next(
        stream for stream in probe["streams"] if stream["codec_type"] == "video"
    )
    width = int(video_info["width"])
    height = int(video_info["height"])
    fps = float(video_info["r_frame_rate"].split("/")[0]) / float(
        video_info["r_frame_rate"].split("/")[1]
    )
    codec = video_info["codec_name"]
    num_frames = int(probe["streams"][0]["nb_frames"])
    # Open the input video
    process1 = (
        ffmpeg.input(input_path)
        .output(
            "pipe:",
            format="rawvideo",
            pix_fmt="rgb24",
            s="{}x{}".format(width, height),
            r=fps,
        )
        .global_args("-nostats", "-loglevel", "error")
        .run_async(pipe_stdout=True, pipe_stderr=False)
    )
    # Open the output video with optimal thread usage.
    process2 = (
        ffmpeg.input(
            "pipe:",
            format="rawvideo",
            pix_fmt="rgb24",
            s="{}x{}".format(width, height),
            r=fps,
        )
        .output(full_path, vcodec="libx264", pix_fmt="yuv420p", r=fps)
        .overwrite_output()
        .global_args("-nostats", "-loglevel", "error")
        .run_async(pipe_stdin=True, pipe_stderr=False)
    )

    # Create a random message
    # msgs = model.get_random_msg()
    # print(msgs.shape)
    # Your watermark message (string)
    msg_string = watermark  # You can replace this with any 6-character string

# Convert to 256-bit message
    msgs = string_to_bit_tensor(msg_string, target_length=256)
    # Save original string (for reference)
    with open(full_path.replace(".mp4", ".txt"), "w") as f:
        f.write(msg_string)
    with open(full_path.replace(".mp4", ".txt"), "w") as f:
        f.write("".join([str(msg.item()) for msg in msgs[0]]))
    # Process the video
    frame_size = width * height * 3
    chunk = np.zeros((chunk_size, height, width, 3), dtype=np.uint8)
    frames_in_chunk = 0

    for in_bytes in tqdm.tqdm(
        iter(lambda: process1.stdout.read(frame_size), b""),
        total=num_frames,
        desc="Watermark embedding",
    ):
        # Convert bytes to frame and add to chunk
        frame = np.frombuffer(in_bytes, np.uint8).reshape([height, width, 3])
        chunk[frames_in_chunk] = frame
        frames_in_chunk += 1

        # Process chunk when full
        if frames_in_chunk == chunk_size:
            # print(f"embedding at frame: {frame_idx}")
            processed_frames = embed_video_clip(model, chunk, msgs)
            process2.stdin.write(processed_frames.tobytes())
            frames_in_chunk = 0

    # Process final partial chunk if any
    if frames_in_chunk > 0:
        processed_frames = embed_video_clip(model, chunk[:frames_in_chunk], msgs)
        process2.stdin.write(processed_frames.tobytes())

    process1.stdout.close()
    process2.stdin.close()
    process1.wait()
    process2.wait()

    return msgs


def detect_video_clip(model: Videoseal, clip: np.ndarray) -> torch.Tensor:
    clip_tensor = torch.tensor(clip, dtype=torch.float32).permute(0, 3, 1, 2) / 255.0
    outputs = model.detect(clip_tensor, is_video=True)
    output_bits = outputs["preds"][
        :, 1:
    ]  # exclude the first which may be used for detection
    return output_bits


def detect_video(model: Videoseal, input_path: str, chunk_size: int) -> None:
    # Normalize path to avoid cwd issues
    input_path = os.path.abspath(input_path)
    # Read video dimensions
    probe = ffmpeg.probe(input_path)
    video_info = next(
        stream for stream in probe["streams"] if stream["codec_type"] == "video"
    )
    width = int(video_info["width"])
    height = int(video_info["height"])
    codec = video_info["codec_name"]
    num_frames = int(probe["streams"][0]["nb_frames"])

    # Open the input video
    process1 = (
        ffmpeg.input(input_path)
        .output("pipe:", format="rawvideo", pix_fmt="rgb24")
        .global_args("-nostats", "-loglevel", "error")
        .run_async(pipe_stdout=True, pipe_stderr=False)
    )

    # Process the video
    frame_size = width * height * 3
    chunk = np.zeros((chunk_size, height, width, 3), dtype=np.uint8)
    frame_count = 0
    soft_msgs = []
    pbar = tqdm.tqdm(total=num_frames, desc="Watermark extraction")
    while True:
        in_bytes = process1.stdout.read(frame_size)
        if not in_bytes:
            break
        frame = np.frombuffer(in_bytes, np.uint8).reshape([height, width, 3])
        chunk[frame_count % chunk_size] = frame
        frame_count += 1
        pbar.update(1)
        if frame_count % chunk_size == 0:
            soft_msgs.append(detect_video_clip(model, chunk))
    process1.stdout.close()
    process1.wait()

    soft_msgs = torch.cat(soft_msgs, dim=0)
    soft_msgs = soft_msgs.mean(dim=0)  # Average the predictions across all frames
    return soft_msgs



def extract_mp4_dct(input_file):
    """DCT算法提取 - MP4格式专用"""
    print("video_watermark_extract for MP4!")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    video_model = videoseal.load("videoseal")
    video_model.eval()
    video_model.to(device)
    video_model.compile()

    soft_msgs = detect_video(video_model, input_file, 16)
    extracted_string = bit_tensor_to_string(soft_msgs, max_chars=32)
    print(f"Extracted watermark (as string): {extracted_string}")
    return extracted_string

def extract_avi_dct(input_file):
    """DCT算法提取 - avi格式专用"""
    print("video_watermark_extract for MP4!")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    video_model = videoseal.load("videoseal")
    video_model.eval()
    video_model.to(device)
    video_model.compile()

    soft_msgs = detect_video(video_model, input_file, 16)
    extracted_string = bit_tensor_to_string(soft_msgs, max_chars=32)
    print(f"Extracted watermark (as string): {extracted_string}")
    return extracted_string




# MOV格式的DCT实现
def embed_mov_dct(input_file, watermark):
    """DCT算法实现 - MOV格式专用"""
    print("video_watermark_embed for MOV!")
    class Args:
        input = input_file
        output = get_user_dated_embed_dir('video')

    args = Args()
    os.makedirs(args.output, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    video_model = videoseal.load("videoseal")
    video_model.eval()
    video_model.to(device)
    video_model.compile()
    # current_dir = os.getcwd()
    # 文件保存逻辑
    original_name = os.path.basename(args.input)
    name_without_ext = os.path.splitext(original_name)[0]
    # filename = f"{name_without_ext}_embed.{'png'}"
    filename = f"{name_without_ext}_embed.{'mov'}"
    full_path = os.path.join(args.output, filename)
    # output = os.path.join(current_dir, args.output)
    msgs_ori = embed_video(video_model, args.input, args.output, 16, watermark, full_path)

        
    return full_path  # 返回完整路径


def extract_mov_dct(input_file):
    """DCT算法提取 - mov格式专用"""
    print("video_watermark_extract for MOV!")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    video_model = videoseal.load("videoseal")
    video_model.eval()
    video_model.to(device)
    video_model.compile()

    soft_msgs = detect_video(video_model, input_file, 16)
    extracted_string = bit_tensor_to_string(soft_msgs, max_chars=32)
    print(f"Extracted watermark (as string): {extracted_string}")
    return extracted_string

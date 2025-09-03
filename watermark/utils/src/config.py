#!/usr/bin/env python3
"""
WavMark 配置文件
用户可以在这里修改默认设置
"""

# 音频处理参数
AUDIO_CONFIG = {
    'target_sample_rate': 16000,  # 目标采样率
    'target_channels': 1,         # 目标声道数 (1=单声道)
    'supported_formats': ['.wav', '.mp3', '.flac', '.m4a', '.ogg', '.aac']
}

# 水印参数
WATERMARK_CONFIG = {
    'payload_length': 16,         # 载荷长度 (位)
    'min_snr': 25.0,             # 最小信噪比 (dB)
    'max_snr': 35.0,             # 最大信噪比 (dB)
    'show_progress': True         # 显示进度条
}

# 文件处理参数
FILE_CONFIG = {
    'default_input_dir': None,    # 默认输入目录 (None = 自动检测)
    'default_output_dir': None,   # 默认输出目录 (None = 自动检测)
    'output_suffix': '_watermarked',  # 输出文件后缀
    'backup_original': False,     # 是否备份原文件
    'overwrite_existing': True    # 是否覆盖已存在的文件
}

# GPU 设置
GPU_CONFIG = {
    'device': 'cuda',             # 设备类型 ('cuda' 或 'cpu')
    'memory_fraction': 0.8,       # GPU 内存使用比例
    'allow_cpu_fallback': False   # 是否允许 CPU 回退
}

# 性能优化
PERFORMANCE_CONFIG = {
    'batch_size': 1,              # 批处理大小
    'max_workers': 1,             # 最大工作线程数
    'temp_dir': None,             # 临时目录 (None = 自动)
    'cleanup_temp': True          # 清理临时文件
}

# 日志设置
LOG_CONFIG = {
    'level': 'INFO',              # 日志级别
    'format': '%(asctime)s - %(levelname)s - %(message)s',
    'file': None,                 # 日志文件 (None = 控制台输出)
    'console_output': True        # 是否输出到控制台
}

# 质量阈值
QUALITY_THRESHOLDS = {
    'min_ber': 0.01,              # 最大允许比特错误率 (1%)
    'min_snr': 20.0,              # 最小可接受信噪比 (dB)
    'max_processing_time': 300    # 最大处理时间 (秒)
}

def get_config():
    """获取完整配置"""
    return {
        'audio': AUDIO_CONFIG,
        'watermark': WATERMARK_CONFIG,
        'file': FILE_CONFIG,
        'gpu': GPU_CONFIG,
        'performance': PERFORMANCE_CONFIG,
        'log': LOG_CONFIG,
        'quality': QUALITY_THRESHOLDS
    }

def update_config(**kwargs):
    """更新配置"""
    global AUDIO_CONFIG, WATERMARK_CONFIG, FILE_CONFIG, GPU_CONFIG
    global PERFORMANCE_CONFIG, LOG_CONFIG, QUALITY_THRESHOLDS
    
    for key, value in kwargs.items():
        if key == 'audio':
            AUDIO_CONFIG.update(value)
        elif key == 'watermark':
            WATERMARK_CONFIG.update(value)
        elif key == 'file':
            FILE_CONFIG.update(value)
        elif key == 'gpu':
            GPU_CONFIG.update(value)
        elif key == 'performance':
            PERFORMANCE_CONFIG.update(value)
        elif key == 'log':
            LOG_CONFIG.update(value)
        elif key == 'quality':
            QUALITY_THRESHOLDS.update(value)

# 示例：自定义配置
if __name__ == "__main__":
    # 示例：修改水印参数
    update_config(watermark={
        'min_snr': 30.0,  # 提高最小信噪比
        'max_snr': 40.0   # 提高最大信噪比
    })
    
    # 示例：修改文件设置
    update_config(file={
        'output_suffix': '_wm',  # 自定义后缀
        'backup_original': True  # 启用备份
    })
    
    print("配置已更新")
    print("当前配置:", get_config()) 
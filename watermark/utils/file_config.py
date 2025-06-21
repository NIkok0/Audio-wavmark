import os

# 从环境变量获取文件大小限制
def get_max_size_from_env(file_type):
    """从环境变量获取文件类型的最大大小限制"""
    env_mapping = {
        'image': 'IMAGE_MAX_SIZE',
        'audio': 'AUDIO_MAX_SIZE', 
        'video': 'VIDEO_MAX_SIZE',
        'text': 'TEXT_MAX_SIZE'
    }
    
    env_key = env_mapping.get(file_type)
    if env_key:
        return int(os.getenv(env_key, '104857600'))  # 默认100MB
    return int(os.getenv('DEFAULT_MAX_SIZE', '104857600'))

# 文件类型配置 - 支持默认算法和扩展算法
FILE_TYPE_CONFIG = {
    'image': {
        'extensions': ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'gif', 'webp'],
        'mime_types': ['image/jpeg', 'image/png', 'image/bmp', 'image/tiff', 'image/gif', 'image/webp'],
        'max_size': get_max_size_from_env('image'),
        'default_algorithm': 'LSB',  # 默认算法
        'available_algorithms': {    # 可用算法配置
            'LSB': {
                'name': 'LSB隐写',
                'description': '最低有效位隐写算法',
                'implemented': True,  # 是否已实现
                'priority': 1         # 优先级，数字越小优先级越高
            },
            'DCT': {
                'name': 'DCT变换',
                'description': '离散余弦变换水印算法',
                'implemented': False,  # 后期实现
                'priority': 2
            },
            'Cox': {
                'name': 'Cox算法',
                'description': 'Cox鲁棒水印算法',
                'implemented': False,  # 后期实现
                'priority': 3
            },
            'DWT': {
                'name': '小波变换',
                'description': '离散小波变换水印算法',
                'implemented': False,  # 后期实现
                'priority': 4
            }
        }
    },
    'video': {
        'extensions': ['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'mxf'],
        'mime_types': ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-ms-wmv'],
        'max_size': get_max_size_from_env('video'),
        'default_algorithm': 'DCT',
        'available_algorithms': {
            'DCT': {
                'name': 'DCT变换',
                'description': '视频DCT水印算法',
                'implemented': True,
                'priority': 1
            },
            'Cox': {
                'name': 'Cox算法',
                'description': '视频Cox鲁棒水印算法',
                'implemented': False,
                'priority': 2
            },
            'LSB': {
                'name': 'LSB隐写',
                'description': '视频LSB隐写算法',
                'implemented': False,
                'priority': 3
            }
        }
    },
    'audio': {
        'extensions': ['mp3', 'wav', 'flac', 'aac', 'ogg'],
        'mime_types': ['audio/mpeg', 'audio/wav', 'audio/flac', 'audio/aac'],
        'max_size': get_max_size_from_env('audio'),
        'default_algorithm': 'LSB',
        'available_algorithms': {
            'LSB': {
                'name': 'LSB隐写',
                'description': '音频LSB隐写算法',
                'implemented': True,
                'priority': 1
            },
            'DCT': {
                'name': 'DCT变换',
                'description': '音频DCT水印算法',
                'implemented': False,
                'priority': 2
            },
            'Cox': {
                'name': 'Cox算法',
                'description': '音频Cox鲁棒水印算法',
                'implemented': False,
                'priority': 3
            }
        }
    },
    'text': {
        'extensions': ['txt', 'pdf', 'docx', 'doc', 'rtf'],
        'mime_types': ['text/plain', 'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
        'max_size': get_max_size_from_env('text'),
        'default_algorithm': 'LSB',
        'available_algorithms': {
            'LSB': {
                'name': 'LSB隐写',
                'description': '文本LSB隐写算法',
                'implemented': True,
                'priority': 1
            },
            'DCT': {
                'name': 'DCT变换',
                'description': '文本DCT水印算法',
                'implemented': False,
                'priority': 2
            }
        }
    }
}

def get_file_type_by_extension(extension):
    """根据文件扩展名获取文件类型"""
    extension = extension.lower()
    for file_type, config in FILE_TYPE_CONFIG.items():
        if extension in config['extensions']:
            return file_type
    return None

def get_default_algorithm(file_type):
    """获取文件类型的默认算法"""
    if file_type in FILE_TYPE_CONFIG:
        return FILE_TYPE_CONFIG[file_type]['default_algorithm']
    return 'LSB'

def get_implemented_algorithms(file_type):
    """获取已实现的算法列表（按优先级排序）"""
    if file_type not in FILE_TYPE_CONFIG:
        return ['LSB']
    
    algorithms = FILE_TYPE_CONFIG[file_type]['available_algorithms']
    implemented = [(name, config) for name, config in algorithms.items() if config['implemented']]
    
    # 按优先级排序
    implemented.sort(key=lambda x: x[1]['priority'])
    return [name for name, _ in implemented]

def get_all_available_algorithms(file_type):
    """获取所有可用算法（包括未实现的）"""
    if file_type not in FILE_TYPE_CONFIG:
        return ['LSB']
    
    algorithms = FILE_TYPE_CONFIG[file_type]['available_algorithms']
    return list(algorithms.keys())

def is_algorithm_implemented(file_type, algorithm):
    """检查算法是否已实现"""
    if file_type not in FILE_TYPE_CONFIG:
        return algorithm == 'LSB'
    
    algorithms = FILE_TYPE_CONFIG[file_type]['available_algorithms']
    return algorithm in algorithms and algorithms[algorithm]['implemented']

def get_algorithm_info(file_type, algorithm):
    """获取算法详细信息"""
    if file_type not in FILE_TYPE_CONFIG:
        return None
    
    algorithms = FILE_TYPE_CONFIG[file_type]['available_algorithms']
    return algorithms.get(algorithm)

def get_allowed_extensions():
    """获取所有支持的文件扩展名"""
    all_extensions = []
    for config in FILE_TYPE_CONFIG.values():
        all_extensions.extend(config['extensions'])
    return all_extensions

def validate_file_size(file_size, file_type=None):
    """验证文件大小是否在允许范围内"""
    if file_type and file_type in FILE_TYPE_CONFIG:
        max_size = FILE_TYPE_CONFIG[file_type]['max_size']
        return file_size <= max_size
    return True

def get_file_size_info(file_type):
    """获取文件类型的大小限制信息"""
    if file_type and file_type in FILE_TYPE_CONFIG:
        max_size = FILE_TYPE_CONFIG[file_type]['max_size']
        return {
            'max_size': max_size
        }
    return None

def format_file_size(size_bytes):
    """格式化文件大小显示"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {size_names[i]}" 
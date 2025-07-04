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
        'extensions': {
            'jpg': {
                'mime_type': 'image/jpeg',
                'algorithms': {
                    'LSB': {
                        'name': 'LSB隐写',
                        'description': '最低有效位隐写算法',
                        'implemented': True,
                        'priority': 1
                    },
                    'DCT': {
                        'name': 'DCT变换',
                        'description': '离散余弦变换水印算法',
                        'implemented': False,
                        'priority': 2
                    },
                    'Cox': {
                        'name': 'Cox算法',
                        'description': 'Cox鲁棒水印算法',
                        'implemented': False,
                        'priority': 3
                    },
                    'DWT': {
                        'name': '小波变换',
                        'description': '离散小波变换水印算法',
                        'implemented': False,
                        'priority': 4
                    }
                },
                'default_algorithm': 'LSB'
            },
            'jpeg': {
                'mime_type': 'image/jpeg',
                'algorithms': {
                    'LSB': {
                        'name': 'LSB隐写',
                        'description': '最低有效位隐写算法',
                        'implemented': True,
                        'priority': 1
                    },
                    'DCT': {
                        'name': 'DCT变换',
                        'description': '离散余弦变换水印算法',
                        'implemented': False,
                        'priority': 2
                    }
                },
                'default_algorithm': 'LSB'
            },
            'png': {
                'mime_type': 'image/png',
                'algorithms': {
                    'LSB': {
                        'name': 'LSB隐写',
                        'description': '最低有效位隐写算法',
                        'implemented': True,
                        'priority': 1
                    }
                },
                'default_algorithm': 'LSB'
            },
            'bmp': {
                'mime_type': 'image/bmp',
                'algorithms': {
                    'LSB': {
                        'name': 'LSB隐写',
                        'description': '最低有效位隐写算法',
                        'implemented': True,
                        'priority': 1
                    }
                },
                'default_algorithm': 'LSB'
            }
        },
        'max_size': get_max_size_from_env('image')
    },
    'video': {
        'extensions': {
            'mp4': {
                'mime_type': 'video/mp4',
                'algorithms': {
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
                    }
                },
                'default_algorithm': 'DCT'
            },
            'avi': {
                'mime_type': 'video/avi',
                'algorithms': {
                    'DCT': {
                        'name': 'DCT变换',
                        'description': '视频DCT水印算法',
                        'implemented': True,
                        'priority': 1
                    }
                },
                'default_algorithm': 'DCT'
            },
            'mxf': {
                'mime_type': 'application/mxf',
                'algorithms': {
                    'DCT': {
                        'name': 'DCT变换',
                        'description': '视频DCT水印算法',
                        'implemented': True,
                        'priority': 1
                    }
                },
                'default_algorithm': 'DCT'
            }
        },
        'max_size': get_max_size_from_env('video')
    },
    'audio': {
        'extensions': {
            'ogg': {
                'mime_type': 'audio/ogg',
                'algorithms': {
                    'LSB': {
                        'name': 'LSB隐写',
                        'description': '音频LSB隐写算法',
                        'implemented': True,
                        'priority': 1
                    }
                },
                'default_algorithm': 'LSB'
            },
            'mp3': {
                'mime_type': 'audio/mpeg',
                'algorithms': {
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
                    }
                },
                'default_algorithm': 'LSB'
            },
            'wav': {
                'mime_type': 'audio/wav',
                'algorithms': {
                    'LSB': {
                        'name': 'LSB隐写',
                        'description': '音频LSB隐写算法',
                        'implemented': True,
                        'priority': 1
                    }
                },
                'default_algorithm': 'LSB'
            }
        },
        'max_size': get_max_size_from_env('audio')
    },
    'text': {
        'extensions': {
            'txt': {
                'mime_type': 'text/plain',
                'algorithms': {
                    'LSB': {
                        'name': 'LSB隐写',
                        'description': '文本LSB隐写算法',
                        'implemented': True,
                        'priority': 1
                    }
                },
                'default_algorithm': 'LSB'
            },
            'pdf': {
                'mime_type': 'application/pdf',
                'algorithms': {
                    'LSB': {
                        'name': 'LSB隐写',
                        'description': '文本LSB隐写算法',
                        'implemented': True,
                        'priority': 1
                    }
                },
                'default_algorithm': 'LSB'
            }
        },
        'max_size': get_max_size_from_env('text')
    }
}

def get_file_type_by_extension(extension):
    """根据文件扩展名获取文件类型"""
    extension = extension.lower()
    for file_type, config in FILE_TYPE_CONFIG.items():
        if extension in config['extensions']:
            return file_type
    return None

def get_default_algorithm(extension):
    """获取文件扩展名的默认算法"""
    extension = extension.lower()
    file_type = get_file_type_by_extension(extension)
    if file_type and extension in FILE_TYPE_CONFIG[file_type]['extensions']:
        return FILE_TYPE_CONFIG[file_type]['extensions'][extension]['default_algorithm']
    return 'LSB'

def get_implemented_algorithms(extension):
    """获取指定文件扩展名的已实现算法列表（按优先级排序）"""
    extension = extension.lower()
    file_type = get_file_type_by_extension(extension)
    if not file_type or extension not in FILE_TYPE_CONFIG[file_type]['extensions']:
        return ['LSB']
    
    algorithms = FILE_TYPE_CONFIG[file_type]['extensions'][extension]['algorithms']
    implemented = [(name, config) for name, config in algorithms.items() if config['implemented']]
    
    # 按优先级排序
    implemented.sort(key=lambda x: x[1]['priority'])
    return [name for name, _ in implemented]

def get_all_available_algorithms(extension):
    """获取指定文件扩展名的所有可用算法（包括未实现的）"""
    extension = extension.lower()
    file_type = get_file_type_by_extension(extension)
    if not file_type or extension not in FILE_TYPE_CONFIG[file_type]['extensions']:
        return ['LSB']
    
    return list(FILE_TYPE_CONFIG[file_type]['extensions'][extension]['algorithms'].keys())

def is_algorithm_implemented(extension, algorithm):
    """检查指定文件扩展名的算法是否已实现"""
    extension = extension.lower()
    file_type = get_file_type_by_extension(extension)
    if not file_type or extension not in FILE_TYPE_CONFIG[file_type]['extensions']:
        return algorithm == 'LSB'
    
    algorithms = FILE_TYPE_CONFIG[file_type]['extensions'][extension]['algorithms']
    return algorithm in algorithms and algorithms[algorithm]['implemented']

def get_algorithm_info(extension, algorithm):
    """获取指定文件扩展名的算法详细信息"""
    extension = extension.lower()
    file_type = get_file_type_by_extension(extension)
    if not file_type or extension not in FILE_TYPE_CONFIG[file_type]['extensions']:
        return None
    
    algorithms = FILE_TYPE_CONFIG[file_type]['extensions'][extension]['algorithms']
    return algorithms.get(algorithm)

def get_allowed_extensions():
    """获取所有支持的文件扩展名"""
    all_extensions = []
    for config in FILE_TYPE_CONFIG.values():
        all_extensions.extend(config['extensions'].keys())
    return all_extensions

def validate_file_size(file_size, extension):
    """验证文件大小是否在允许范围内"""
    extension = extension.lower()
    file_type = get_file_type_by_extension(extension)
    if file_type:
        max_size = FILE_TYPE_CONFIG[file_type]['max_size']
        return file_size <= max_size
    return True

def get_file_size_info(extension):
    """获取文件扩展名对应的大小限制信息"""
    extension = extension.lower()
    file_type = get_file_type_by_extension(extension)
    if file_type:
        max_size = FILE_TYPE_CONFIG[file_type]['max_size']
        return {
            'max_size': max_size
        }
    return None

def get_mime_type(extension):
    """获取文件扩展名对应的MIME类型"""
    extension = extension.lower()
    file_type = get_file_type_by_extension(extension)
    if file_type and extension in FILE_TYPE_CONFIG[file_type]['extensions']:
        return FILE_TYPE_CONFIG[file_type]['extensions'][extension]['mime_type']
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
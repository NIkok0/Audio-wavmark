import logging
import os
from watermark.utils.file_config import (
    get_implemented_algorithms, 
    get_default_algorithm,
    get_file_type_by_extension
)
from watermark.utils import watermark_image, watermark_video, watermark_audio, watermark_text
from watermark.utils.watermark_video import text_to_6char_hash
class AlgorithmSelector:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 媒体类型到模块的映射
        self.modules = {
            "image": watermark_image,
            "video": watermark_video,
            "audio": watermark_audio,
            "text": watermark_text
        }
    
    def select_algorithm(self, file_path, watermark_text,random_seed=None):
        """智能选择算法进行水印嵌入"""
        # 获取文件后缀
        _, extension = os.path.splitext(file_path)
        extension = extension[1:].lower()  # 去掉点号并转小写
        
        # 获取文件类型
        file_type = get_file_type_by_extension(extension)
        if not file_type:
            raise ValueError(f"不支持的文件后缀: {extension}")
        print(file_type)
        # 验证文件类型
        if file_type not in self.modules:
            raise ValueError(f"不支持的文件类型: {file_type}, 支持的类型: {list(self.modules.keys())}")
        
        # 获取已实现的算法列表（按优先级排序）
        implemented_algorithms = get_implemented_algorithms(extension)
        
        if not implemented_algorithms:
            raise Exception(f"文件后缀 {extension} 没有可用的算法")
        
        # 优先使用默认算法
        default_algorithm = get_default_algorithm(extension)
        
        # 如果默认算法已实现，优先使用
        if default_algorithm in implemented_algorithms:
            algorithms_to_try = [default_algorithm] + [alg for alg in implemented_algorithms if alg != default_algorithm]
        else:
            algorithms_to_try = implemented_algorithms
        
        # 尝试每个算法
        for algorithm in algorithms_to_try:
            try:
                self.logger.info(f"尝试使用算法 {algorithm} 处理文件 {file_path}")
                if random_seed:
                    result,watermark_hash = self._try_algorithm(algorithm, file_path, watermark_text,random_seed)
                    if result:
                        self.logger.info(f"算法 {algorithm} 处理成功")
                        return {
                            'success': True,
                            'algorithm': algorithm,
                            'result': result,
                            'watermark_hash': watermark_hash
                        }
                    else:
                        self.logger.warning(f"算法 {algorithm} 处理失败，结果无效")
                else:
                    result = self._try_algorithm(algorithm, file_path, watermark_text)
                    if result:
                        self.logger.info(f"算法 {algorithm} 处理成功")
                        return {
                            'success': True,
                            'algorithm': algorithm,
                            'result': result
                        }
                    else:
                        self.logger.warning(f"算法 {algorithm} 处理失败，结果无效")
                    
            except Exception as e:
                self.logger.error(f"算法 {algorithm} 处理出错: {str(e)}")
                continue
        
        # 所有算法都失败了
        raise Exception(f"所有可用算法都无法处理该文件")
    
    def _try_algorithm(self, algorithm, file_path, watermark_text,random_seed=None):
        """尝试使用指定算法处理文件"""
        # 获取文件类型
        _, extension = os.path.splitext(file_path)
        extension = extension[1:].lower()
        file_type = get_file_type_by_extension(extension)
        if not file_type:
            raise ValueError(f"不支持的文件后缀: {extension}")

        # 验证文件类型
        if file_type not in self.modules:
            raise ValueError(f"不支持的文件类型: {file_type}, 支持的类型: {list(self.modules.keys())}")

        # 获取对应的模块
        module = self.modules[file_type]

        # 动态获取embed函数并调用
        embed_func = getattr(module, "embed")
        if random_seed:
            result,watermark_hash = embed_func(file_path, watermark_text, algorithm,random_seed)
            return result,watermark_hash
        else:
            result = embed_func(file_path, watermark_text, algorithm)
            return result

    def extract_watermark(self, file_path, algorithm=None,watermark_seed=None,watermark_text=None,original_watermark_text=None):
        """提取水印"""
        # 获取文件后缀和类型
        _, extension = os.path.splitext(file_path)
        extension = extension[1:].lower()
        file_type = get_file_type_by_extension(extension)
        if not file_type:
            raise ValueError(f"不支持的文件后缀: {extension}")
        # 1. 验证文件类型
        if file_type not in self.modules:
            raise ValueError(f"不支持的文件类型: {file_type}, 支持的类型: {list(self.modules.keys())}")
        # 2. 获取对应的模块
        module = self.modules[file_type]
        # 3. 动态获取extract函数并调用
        extract_func = getattr(module, "extract")
        if watermark_seed:
            print("开始计算水印hash")
            watermark_hash_after = extract_func(file_path, algorithm)
            if str(watermark_hash_after) != str(watermark_text):
                raise ValueError("水印hash不匹配")
            return original_watermark_text
        else:
            result = extract_func(file_path, algorithm)
            return result

    def extract_watermark_try_all(self, file_path):
        """尝试所有算法提取水印，直到成功"""
        # 获取文件后缀和类型
        _, extension = os.path.splitext(file_path)
        extension = extension[1:].lower()
        file_type = get_file_type_by_extension(extension)
        
        if not file_type:
            raise ValueError(f"不支持的文件后缀: {extension}")
        
        if file_type not in self.modules:
            raise ValueError(f"不支持的文件类型: {file_type}")
        
        # 获取该文件类型的所有已实现算法
        implemented_algorithms = get_implemented_algorithms(extension)
        
        if not implemented_algorithms:
            raise Exception(f"文件后缀 {extension} 没有可用的算法")
        
        # 优先尝试默认算法
        default_algorithm = get_default_algorithm(extension)
        if default_algorithm in implemented_algorithms:
            algorithms_to_try = [default_algorithm] + [alg for alg in implemented_algorithms if alg != default_algorithm]
        else:
            algorithms_to_try = implemented_algorithms
        
        # 获取对应的模块
        module = self.modules[file_type]
        extract_func = getattr(module, "extract")
        
        # 收集每个算法的尝试结果
        attempt_results = []
        
        # 尝试每个算法
        for algorithm in algorithms_to_try:
            try:
                self.logger.info(f"尝试使用算法 {algorithm} 提取水印 from {file_path}")
                result = extract_func(file_path, algorithm)
                
                # 检查结果是否有效
                if result and result.strip():
                    self.logger.info(f"算法 {algorithm} 成功提取水印: {result}")
                    attempt_results.append({
                        'algorithm': algorithm,
                        'status': 'success',
                        'message': f'成功提取水印'
                    })
                    return result, algorithm, attempt_results
                else:
                    error_msg = f"提取结果为空"
                    self.logger.warning(f"算法 {algorithm} {error_msg}")
                    attempt_results.append({
                        'algorithm': algorithm,
                        'status': 'empty',
                        'message': error_msg
                    })
                    
            except Exception as e:
                error_msg = str(e)
                self.logger.error(f"算法 {algorithm} 提取失败: {error_msg}")
                attempt_results.append({
                    'algorithm': algorithm,
                    'status': 'error',
                    'message': error_msg
                })
                continue
        
        # 所有算法都失败了
        error_msg = f"尝试了所有可用算法 {algorithms_to_try}，均无法提取水印"
        raise Exception(error_msg, attempt_results)





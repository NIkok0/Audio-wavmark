# -*- coding: utf-8 -*-
"""
Windows Server 兼容性工具模块
解决Windows Server环境下的路径、权限和OpenCV相关问题
"""

import os
import sys
import platform


def is_windows_server():
    """检测是否运行在Windows Server上"""
    if platform.system() != 'Windows':
        return False
    
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
        product_name, _ = winreg.QueryValueEx(key, "ProductName")
        winreg.CloseKey(key)
        return 'Server' in product_name
    except:
        return False


def normalize_path(path):
    """
    规范化路径，确保Windows兼容性
    
    Args:
        path: 输入路径
        
    Returns:
        规范化后的路径
    """
    if not path:
        return path
    
    # 转换为字符串
    path = str(path)
    
    # 规范化路径分隔符
    path = os.path.normpath(path)
    
    # 如果是相对路径，转换为绝对路径
    if not os.path.isabs(path):
        path = os.path.abspath(path)
    
    return path


def ensure_directory_exists(directory, verbose=True):
    """
    确保目录存在，Windows兼容版本
    
    Args:
        directory: 目录路径
        verbose: 是否打印详细信息
        
    Returns:
        bool: 是否成功创建或目录已存在
    """
    try:
        directory = normalize_path(directory)
        
        if os.path.exists(directory):
            if verbose:
                print(f"[INFO] 目录已存在: {directory}")
            return True
        
        # 在Windows上不使用mode参数
        os.makedirs(directory, exist_ok=True)
        
        if verbose:
            print(f"[SUCCESS] 创建目录成功: {directory}")
        return True
        
    except PermissionError as e:
        print(f"[ERROR] 权限不足，无法创建目录: {directory}")
        print(f"[ERROR] 错误详情: {str(e)}")
        print(f"[HINT] 请检查当前用户是否有该路径的写入权限")
        return False
        
    except Exception as e:
        print(f"[ERROR] 创建目录失败: {directory}")
        print(f"[ERROR] 错误详情: {str(e)}")
        
        # 尝试使用系统临时目录
        try:
            import tempfile
            temp_dir = tempfile.gettempdir()
            fallback_dir = os.path.join(temp_dir, os.path.basename(directory))
            os.makedirs(fallback_dir, exist_ok=True)
            print(f"[FALLBACK] 使用备用目录: {fallback_dir}")
            return fallback_dir
        except:
            return False


def check_opencv_compatibility():
    """
    检查OpenCV在Windows Server上的兼容性
    """
    try:
        import cv2
        print(f"[INFO] OpenCV版本: {cv2.__version__}")
        
        # 测试基本功能
        import numpy as np
        test_img = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # 测试编码
        success, buffer = cv2.imencode('.jpg', test_img)
        if success:
            print("[SUCCESS] OpenCV JPEG编码测试通过")
        else:
            print("[WARNING] OpenCV JPEG编码测试失败")
            
        # 测试PNG编码
        success, buffer = cv2.imencode('.png', test_img)
        if success:
            print("[SUCCESS] OpenCV PNG编码测试通过")
        else:
            print("[WARNING] OpenCV PNG编码测试失败")
            
        return True
        
    except ImportError:
        print("[ERROR] OpenCV未安装或无法导入")
        return False
    except Exception as e:
        print(f"[ERROR] OpenCV兼容性检查失败: {str(e)}")
        return False


def check_blind_watermark_compatibility():
    """
    检查blind_watermark库的兼容性
    """
    try:
        from blind_watermark import WaterMark
        print("[SUCCESS] blind_watermark库导入成功")
        
        # 测试基本功能
        import tempfile
        import numpy as np
        from PIL import Image
        
        # 创建测试图像
        temp_dir = tempfile.gettempdir()
        test_img_path = os.path.join(temp_dir, "test_watermark.png")
        test_output_path = os.path.join(temp_dir, "test_watermark_embed.png")
        
        # 创建简单的测试图像
        img = Image.new('RGB', (512, 512), color='white')
        img.save(test_img_path)
        
        # 测试嵌入
        wm = WaterMark(password_img=1, password_wm=1)
        wm.read_img(test_img_path)
        wm.read_wm("测试水印水印水印印水", mode='str')
        wm.embed(test_output_path)
        
        if os.path.exists(test_output_path):
            print("[SUCCESS] blind_watermark嵌入测试通过")
            
            # 清理测试文件
            try:
                os.remove(test_img_path)
                os.remove(test_output_path)
            except:
                pass
            
            return True
        else:
            print("[WARNING] blind_watermark嵌入测试失败：输出文件未创建")
            return False
            
    except ImportError:
        print("[ERROR] blind_watermark库未安装或无法导入")
        return False
    except Exception as e:
        print(f"[ERROR] blind_watermark兼容性检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_diagnostics():
    """
    运行完整的Windows Server兼容性诊断
    """
    print("=" * 60)
    print("Windows Server 兼容性诊断")
    print("=" * 60)
    
    # 系统信息
    print(f"\n[系统信息]")
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"Python版本: {sys.version}")
    print(f"是否为Windows Server: {is_windows_server()}")
    
    # 检查OpenCV
    print(f"\n[OpenCV检查]")
    opencv_ok = check_opencv_compatibility()
    
    # 检查blind_watermark
    print(f"\n[blind_watermark检查]")
    watermark_ok = check_blind_watermark_compatibility()
    
    # 检查目录权限
    print(f"\n[目录权限检查]")
    test_dirs = [
        'instance',
        'instance/temp',
        'instance/uploads/images',
        'instance/embeds/images',
        'instance/extracts/images'
    ]
    
    for test_dir in test_dirs:
        result = ensure_directory_exists(test_dir, verbose=False)
        status = "[OK]" if result else "[FAIL]"
        print(f"{status} {test_dir}")
    
    # 总结
    print(f"\n[诊断总结]")
    if opencv_ok and watermark_ok:
        print("[SUCCESS] 所有核心组件检查通过")
    else:
        print("[WARNING] 部分组件检查失败，请查看上述详细信息")
    
    print("=" * 60)


if __name__ == '__main__':
    run_diagnostics()


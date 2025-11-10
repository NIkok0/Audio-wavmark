#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Windows Server 兼容性检查脚本
在部署到Windows Server前运行此脚本进行诊断
"""

import sys
import os

# 添加项目路径到sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from watermark.utils.windows_compat import run_diagnostics

if __name__ == '__main__':
    print("开始Windows Server兼容性检查...\n")
    run_diagnostics()
    print("\n检查完成！")


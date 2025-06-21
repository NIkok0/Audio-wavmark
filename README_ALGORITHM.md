# 水印算法集成指南

## 目录
1. [项目结构](#项目结构)
2. [添加新算法步骤](#添加新算法步骤)
3. [算法接口规范](#算法接口规范)
4. [示例](#示例)

## 项目结构

本项目采用模块化设计，所有水印算法相关的代码都位于 `watermark/utils/` 目录下：

```
watermark/utils/
├── file_config.py  # 算法配置文件
├── algorithm_selector.py  # 算法选择器
├── watermark_audio.py    # 音频水印算法
├── watermark_image.py    # 图像水印算法
├── watermark_text.py     # 文本水印算法
└── watermark_video.py    # 视频水印算法
```

## 添加新算法步骤
首先需要在算法的配置文件中依照自己的算法名称进行创建自己算法的配置条目
在FILE_TYPE_CONFIG中找到自己的媒体种类
随后添加自己的算法配置在available_algorithms

1. **选择对应的文件**
   - 根据你的算法类型，选择对应的文件：
     - 图像水印 → watermark_image.py
     - 音频水印 → watermark_audio.py
     - 视频水印 → watermark_video.py
     - 文本水印 → watermark_text.py

2. **实现嵌入函数**
   - 在对应文件中创建新的算法函数
   - 函数名格式：`embed_lsb(input_file, watermark)`
   - 函数名的前半部分是操作--嵌入或提取embed extract
   - 后半部分是刚刚在file_config你注册的函数名的小写比如刚刚在FILE_TYPE_CONFIG写的LSB算法这里就要写lsb
   - 函数的输入为准备嵌入算法的文件的路径需要自己通过文件路径读取文件，watermark是嵌入的信息
   -输出的嵌入后的文件本身
    `return im_embed`
3. **实现提取函数**
   -  同嵌入函数 `extract_lsb(input_file)`
   - 需要自己读取input_file ，input_file是文件路径
   - 输出的是嵌入的信息`return result `

## 自动化过程
1. **前端页面到view页面中的路由处理**
2. **路由处理逻辑交由算法选择器`AlgorithmSelector()` 在algorithm_selector.py之中**
3. **算法选择器会判断到哪个utils文件中**
4. **utils函数也会自动选择**
5. **需要保证函数的名称命名好，同时file_config配置好**


# 数字水印系统

一个基于Flask的数字水印系统，支持对图片、音频、视频和文本文件添加和提取数字水印。

## 功能特点

### 支持的媒体类型
- **图片水印**: 支持JPG、JPEG、PNG、BMP、GIF格式
- **音频水印**: 支持MP3、WAV、FLAC、AAC格式
- **视频水印**: 支持MP4、AVI、MKV、MOV格式
- **文本水印**: 支持TXT、DOC、DOCX、PDF格式

### 核心功能
- **添加水印**: 为各种媒体文件添加不可见的数字水印
- **提取水印**: 从已添加水印的文件中提取水印信息
- **批量处理**: 支持批量上传和批量添加水印
- **文件管理**: 完整的文件上传、下载、删除管理功能
- **算法扩展**: 支持自定义水印算法的快速集成

### 水印算法
- **模块化设计**: 支持不同类型媒体的算法独立开发和集成
- **算法配置**: 通过配置文件灵活管理可用算法
- **自动化集成**: 提供标准接口规范，支持新算法的快速接入
- **详细文档**: 提供完整的算法集成指南（参见 README_ALGORITHM.md）

### 批量上传和选择功能

#### 批量上传功能
- **多文件选择**: 支持同时选择多个文件进行上传
- **拖拽上传**: 支持拖拽多个文件到上传区域
- **上传队列**: 实时显示上传进度和状态
- **批量操作**: 支持全选、删除选中文件等批量操作

#### 文件选择功能
- **预选文件**: 从上传页面选择文件后，自动跳转到添加水印页面并预选文件
- **文件选择**: 在添加水印页面可以选择特定文件进行水印添加
- **选中显示**: 实时显示已选择的文件列表
- **批量添加**: 支持为选中的多个文件同时添加水印

## 技术架构

### 后端技术栈
- **Flask**: Web框架
- **SQLAlchemy**: ORM数据库操作
- **Alembic**: 数据库迁移管理
- **Pillow**: 图像处理
- **OpenCV**: 视频处理
- **librosa**: 音频处理
- **PyPDF2**: PDF文档处理

### 前端技术栈
- **Bootstrap**: UI框架
- **jQuery**: JavaScript库
- **HTML5**: 拖拽上传支持
- **CSS3**: 现代化样式
- **Dropzone.js**: 文件上传组件

### 数据库
- **SQLite**: 轻量级数据库（开发环境）
- **MySQL/PostgreSQL**: 生产环境推荐

## 安装和运行

### 环境要求
- Python 3.7+
- FFmpeg (用于视频处理)

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd learn_flask_the_easy_way
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **初始化数据库**
```bash
flask initdb 
```

5. **运行应用**
```bash
flask run
```

访问 http://localhost:5000 即可使用系统。

## 使用指南

### 基本操作流程

1. **上传文件**
   - 进入对应媒体类型的上传页面
   - 支持单个文件上传或批量上传
   - 拖拽文件到上传区域或点击选择文件
   - 批量上传时会显示上传队列和进度

2. **添加水印**
   - 方法一：在上传页面选择文件后，点击"为选中文件添加水印"
   - 方法二：直接进入添加水印页面，选择要处理的文件
   - 选择水印算法并输入水印内容
   - 提交处理请求

3. **提取水印**
   - 上传已添加水印的文件
   - 选择对应的提取算法
   - 系统自动提取并显示水印内容

### 批量操作详细说明

#### 批量上传操作
1. **选择文件**：
   - 点击"选择文件"按钮，按住Ctrl键选择多个文件
   - 或直接拖拽多个文件到上传区域

2. **上传队列**：
   - 选择文件后，系统显示上传队列
   - 每个文件显示状态：等待上传、上传中、上传成功、上传失败
   - 点击"开始上传"按钮开始批量上传

3. **批量管理**：
   - 上传完成后，可以使用全选功能选择所有文件
   - 支持批量删除选中的文件
   - 支持为选中的文件批量添加水印

#### 文件选择功能
1. **预选文件**：
   - 在上传页面选择文件后，点击"为选中文件添加水印"
   - 系统自动跳转到添加水印页面并预选这些文件

2. **手动选择**：
   - 在添加水印页面，可以手动选择要处理的文件
   - 支持全选、单选、取消选择等操作

3. **选中显示**：
   - 实时显示已选择的文件列表
   - 显示选中文件数量
   - 提供清除选择功能

4. **批量添加水印**：
   - 选择文件后，点击"为选中文件添加水印"
   - 系统显示水印添加表单
   - 选择水印算法
   - 输入水印内容后，系统会为所有选中的文件添加相同的水印

### 文件管理功能

- **文件列表**: 显示所有上传的文件，包括文件信息、上传时间、文件大小等
- **状态显示**: 显示文件是否已添加水印、处理状态等
- **批量删除**: 支持选择多个文件进行批量删除
- **下载功能**: 支持下载已添加水印的文件

## 项目结构

```
learn_flask_the_easy_way/
├── watermark/                 # 主应用目录
│   ├── __init__.py           # 应用初始化
│   ├── views.py              # 视图函数
│   ├── models.py             # 数据模型
│   ├── forms/                # 表单定义
│   │   ├── login_form.py     # 登录表单
│   │   ├── register_form.py  # 注册表单
│   │   └── watermark_form.py # 水印表单
│   ├── templates/            # 模板文件
│   │   ├── base.html         # 基础模板
│   │   ├── index.html        # 首页
│   │   ├── register.html     # 注册页面
│   │   ├── signin.html       # 登录页面
│   │   ├── image/            # 图片相关页面
│   │   │   ├── upload.html
│   │   │   ├── add_watermark.html
│   │   │   ├── extract_watermark.html
│   │   │   └── image_process.html
│   │   ├── audio/            # 音频相关页面
│   │   │   ├── upload.html
│   │   │   ├── add_watermark.html
│   │   │   ├── extract_watermark.html
│   │   │   └── audio_process.html
│   │   ├── video/            # 视频相关页面
│   │   │   ├── upload.html
│   │   │   ├── add_watermark.html
│   │   │   ├── extract_watermark.html
│   │   │   └── video_process.html
│   │   └── text/             # 文本相关页面
│   │       ├── upload.html
│   │       ├── add_watermark.html
│   │       ├── extract_watermark.html
│   │       └── text_process.html
│   ├── static/               # 静态文件
│   │   ├── css/              # 样式文件
│   │   │   ├── common.css
│   │   │   ├── custom.css
│   │   │   └── lib/
│   │   └── js/               # JavaScript文件
│   │       ├── common.js
│   │       └── lib/
│   └── utils/                # 工具函数
│       ├── algorithm_selector.py  # 算法选择器
│       ├── file_config.py         # 文件和算法配置
│       ├── watermark_image.py     # 图像水印处理
│       ├── watermark_audio.py     # 音频水印处理
│       ├── watermark_video.py     # 视频水印处理
│       └── watermark_text.py      # 文本水印处理
├── migrations/               # 数据库迁移文件
├── instance/                 # 实例配置
├── test_file/               # 测试文件目录
├── upload/                   # 上传文件存储
├── README.md                 # 项目说明
└── README_ALGORITHM.md       # 算法集成指南
```

## 配置说明

### 环境变量
- `SECRET_KEY`: Flask应用密钥
- `DATABASE_URL`: 数据库连接URL
- `MAX_CONTENT_LENGTH`: 最大文件上传大小

### 文件大小限制
- 图片文件：50MB
- 音频文件：50MB
- 视频文件：500MB

## 算法扩展

本项目支持水印算法的模块化扩展，详细的算法集成指南请参考 [README_ALGORITHM.md](README_ALGORITHM.md)。主要特点包括：

- **标准接口**: 提供统一的算法接口规范
- **自动集成**: 通过配置文件自动加载新算法
- **独立开发**: 支持算法的独立开发和测试
- **文档完备**: 提供详细的开发指南和示例
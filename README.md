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

- **Flask 3.x**: Web 框架，蓝图/上下文/过滤器
- **Flask-SQLAlchemy 3.x**: ORM + 会话管理
- **Flask-Migrate/Alembic**: 数据库迁移
- **Flask-Login**: 认证与会话登录
- **Flask-WTF / WTForms**: 表单与校验（含 email-validator）
- **PyMySQL**: MySQL 驱动（默认连接 MySQL，可切换 SQLite）
- 多媒体处理：
  - **Pillow**（图像），**OpenCV** + **ffmpeg-python**（视频），**NumPy/Scipy**（通用数值/音频），**PyMuPDF/Python-docx**（文档）

### 前端技术栈

- **Bootstrap 5**: 响应式 UI 与组件
- **Chart.js**: 首页可视化（类型饼图、近 14 天趋势折线图）
- **jQuery**: DOM 辅助（少量）
- **Dropzone.js**（可选）: 大文件/多文件上传体验
- **自定义样式**: `static/css/custom.css` 与局部内联样式

### 运行与基础设施

- **数据库**:  **MySQL**（默认 DSN 可在 `.flaskenv`/环境变量中覆盖）
- **迁移**: `flask initdb` 初始化，`flask db migrate/upgrade` 迁移
- **静态资源**: 本地托管 + CDN（Chart.js）

## 安装和运行

### 环境要求

- Python 3.9
- FFmpeg (用于视频、音频流处理)
- FFprobe （用于视频、音频流处理）

### 安装步骤

1. **克隆项目**

```bash
因为项目中存在大文件 并且使用了LFS对大文件进行了托管（github存在100m的文件大小限制）
先安装LFS
第一步：git lfs install

第二步：git clone <repository-url>
拉取仓库的普通文件，此时会把大文件的指针也拉下来

第三步：git lfs pull
拉取大文件

```

2. **创建虚拟环境**

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

或者

```bash
conda 环境创建
（建议使用conda环境）
```

3. **安装依赖**

```bash
pip install -r requirements.txt

安装遇到需要gpu版本的torch使用以下代码
pip install torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu118
```

4. **初始化数据库**

```bash
在.flaskenv中调整自己的mysql数据库密码和端口
```

```bash
$env:FLASK_APP="watermark"
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

## 项目结

```
learn_flask_the_easy_way/
├── watermark/                        # 主应用
│   ├── __init__.py                   # 应用与扩展初始化（DB/Login/Migrate/目录配置）
│   ├── views.py                      # 路由与业务
│   ├── models.py                     # ORM 模型（User/Group/File）
│   ├── commands.py                   # Flask CLI 命令（initdb/create_admin）
│   ├── forms/                        # 表单
│   │   ├── login_form.py
│   │   ├── register_form.py
│   │   └── watermark_form.py
│   ├── templates/                    # 模板
│   │   ├── base.html                 # 全局导航/侧栏/容器
│   │   ├── index.html                # 首页（统计与可视化）
│   │   ├── register.html / signin.html
│   │   ├── image/ (upload/add/extract/process)
│   │   ├── audio/ (upload/add/extract/process)
│   │   ├── video/ (upload/add/extract/process)
│   │   └── text/  (upload/add/extract/process)
│   ├── static/                       # 静态资源
│   │   ├── css/ (custom.css, bootstrap.min.css, 等)
│   │   └── js/  (common.js, bootstrap.bundle.min.js, 等)
│   └── utils/                        # 工具与算法封装
│       ├── configs                   #视频水印算法模型配置文件夹
│       ├── videoseal                 #视频水印算法模型使用工具文件夹
│       ├── src                       #音频水印算法模型使用工具文件夹
│       ├── algorithm_selector.py     # 按文件选择算法/提取算法
│       ├── file_config.py            # 文件类型/大小/算法配置与工具
│       ├── watermark_image.py        # 图像水印
│       ├── watermark_audio.py        # 音频水印
│       ├── watermark_video.py        # 视频水印
│       └── watermark_text.py         # 文本水印
├── migrations/                       # 数据库迁移
├── instance/                         # 运行期生成文件（uploads/embeds/extracts/temp/logs）
├── requirements.txt                  # 依赖清单（固定版本）
├── README.md                         # 项目说明
├── ckpts                             # 视频水印算法模型文件
└── README_ALGORITHM.md               # 算法扩展说明
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

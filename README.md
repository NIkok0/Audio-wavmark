# 数字水印系统

**Web 界面与 HTTP API** 由 **`backend-java`**（Spring Boot、Thymeleaf、`/api/v1/**`）提供；**异步嵌水印**由 Python **`watermark.worker.redis_stream_worker`** 消费 Redis Stream 完成；多媒体算法代码在 **`watermark/`** 目录。支持对图片、音频、视频和文本添加/提取数字水印，以及按用户与日期的文件存储、分页、批量管理与临时文件清理等能力。

## 功能特点

### 支持的媒体类型

- 图片：JPG、JPEG、PNG、BMP、GIF
- 音频：MP3、WAV、FLAC、AAC
- 视频：MP4、AVI、MKV、MOV
- 文本：TXT、DOC、DOCX、PDF、MD、SQL（部分算法）

### 核心功能

- 添加水印：为各媒体文件添加不可见数字水印
- 提取水印：从已加水印文件中提取水印信息
- 批量处理：批量上传、批量添加、批量提取
- 文件管理：上传/下载/删除，支持批量删除（添加页与提取页均支持）
- 权限管理：支持超级管理员/管理员/普通会员角色，可精细控制嵌入/提取权限及账号状态
- 用户设置：支持自定义文件保留天数（过期自动清理），个人资料管理
- 问题反馈：内置问题反馈系统，支持多种反馈类型与表单验证
- 分页展示：上传/添加/提取页面、首页个人列表均支持分页
- 统一提示：前端采用统一的通知样式（替代原生 alert），并修复了验证失败后错误进入“处理中”的问题
- 可视反馈：添加水印表单的输入框支持出错高亮/抖动/行内错误提示
- 存储结构：所有上传/嵌入/提取文件按“用户名/日期(YYYYMMDD)”分层存储
- 中文路径兼容：对含中文路径的图像读写进行临时 ASCII 拷贝适配
- 临时文件清理：处理结束即时删除临时拷贝，另提供独立清理脚本定期清理
- 算法扩展：支持自定义水印算法的标准化接入

### 水印算法

- 模块化：不同媒体算法独立封装
- 配置化：通过 `utils/configs/*.yaml` 管理可用算法
- 接口标准：`utils/watermark_*.py` 暴露统一 `embed/extract` 接口
- 文档：见《README_ALGORITHM.md》

### 批量上传和选择功能

#### 批量上传

- 多文件选择/拖拽上传/上传队列/全选与批量操作

#### 文件选择

- 预选文件：上传页选择后跳转到添加页并自动勾选
- 批量添加/批量提取：对选中文件一次性处理
- 批量删除：添加页与提取页均提供“批量删除”

## 技术架构

### 后端技术栈

- **Spring Boot 3.x**（`backend-java`）：Web、安全、JPA、Flyway、对象存储（COS/MinIO）、任务入队、Thymeleaf 页面
- **MySQL、Redis**：持久化与 Spring Session / 任务队列
- **Python 3.9.23**：水印算法与 Worker（`requirements.txt`；无 Flask Web）
- 多媒体处理：**Pillow**、**ffmpeg**、**Librosa**、**PyMuPDF** 等（见 `watermark/utils`）

### 前端技术栈

- **Thymeleaf** + **Bootstrap 5**（模板与静态资源由 Java 模块提供，Chart.js 等可按需走 CDN）
- **Chart.js**：仪表盘统计
- **Dropzone.js**（可选）：上传体验

### 运行与基础设施

- **数据库 / 结构迁移**：MySQL；表结构由 Java **Flyway** 管理（见 `backend-java`）
- **配置**：本地与生产环境变量见 **`backend-java/README.md`** 与 **`backend-java/deploy/*.env.example`**

## 安装和运行

### 推荐路径（当前架构）

1. **克隆与 Git LFS**（若仓库含大文件）：同下文「克隆项目」步骤。
2. **启动 Java Web + API**：在 **`backend-java`** 下按 **[backend-java/README.md](backend-java/README.md)** 配置 `watermark-api.env`（或 IDE 环境变量），执行 **`mvn -pl web -am spring-boot:run`**（默认 **http://localhost:8080**）。
3. **（可选）本地跑 Python Worker**：Python 3.9.23，`pip install -r requirements.txt`，按 **`watermark/worker/redis_stream_worker.py`** 文件头配置 **`SQLALCHEMY_DATABASE_URI`**、**`WM_REDIS_*`**、**`INSTANCE_PATH`**、COS 等，执行 **`python -m watermark.worker.redis_stream_worker`**。
4. **生产部署**（Nginx、systemd、HTTPS）：**[backend-java/docs/DEPLOY-SERVER.md](backend-java/docs/DEPLOY-SERVER.md)**；技术框架（**纯文本架构图**）见 **[backend-java/docs/watermark-java-backend-tech-selection.md](backend-java/docs/watermark-java-backend-tech-selection.md)**。

### 环境与依赖（Worker / 算法）

- **Python 3.9.23**（Worker 与算法脚本）
- **FFmpeg / FFprobe**（视频、音频）

```bash
python --version
# 期望: Python 3.9.23
```

克隆与 Conda 示例（与历史文档一致，供 Worker 使用）：

```bash
git lfs install
git clone <repository-url>
cd <repository-dir>
git lfs pull

conda create -n watermark python=3.9.23
conda activate watermark
pip install -r requirements.txt
```

以下「使用指南」中的功能描述仍适用；页面路由与模板现由 **`backend-java`** 提供（Thymeleaf），不再使用 **`flask run`** 或 **`.flaskenv`**。

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
   - 选择水印算法并输入水印内容（输入校验失败会有统一样式提示，且不会进入“处理中”状态）
   - 提交处理请求
3. **提取水印**

   - 上传已添加水印的文件
   - 选择对应的提取算法
   - 系统自动提取并显示水印内容（支持批量提取）

### 批量与分页

#### 分页

- 添加页/提取页：水印文件列表均支持分页
- 首页：个人“未添加水印/已添加水印”列表支持独立分页参数（`unwatermarked_page`、`watermarked_page`）
- 分页宏：`backend-java/web/src/main/resources/templates/macros/pagination.html` 支持不同页码参数名称

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

#### 批量删除

- 添加页与提取页均提供“批量删除”按钮，提交到后端 `POST /batch_delete`，按选择的 `file_ids` 删除原文件/水印文件与数据库记录

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

- 文件列表/状态显示/下载/批量删除/分页

### 存储结构与中文路径兼容

- 存储分层：所有文件按 `instance/<uploads|embeds|extracts>/<media>/<username>/<YYYYMMDD>/filename.ext` 组织
- 中文路径：图像算法对含中文路径的读写会自动使用 `instance/temp/` 下的 ASCII 临时拷贝以规避第三方库限制，处理完成后即时删除临时文件
- 临时目录：`TEMP_FOLDER` 默认为 `instance/temp`

## 项目结

```
learn_flask_the_easy_way/
├── wate├── watermark_form.py
│   │   └── permission_form.py        # 权限管理表单
│   ├── templates/                    # 模板
│   │   ├── base.html                 # 全局导航/侧栏/容器
│   │   ├── index.html                # 首页（统计与可视化）
│   │   ├── feedback.html             # 问题反馈页面
│   │   ├── register.html / signin.html
│   │   ├── admin/                    # 管理员页面
│   │   │   └── permission_management.html
│   │   ├── profile/                  # 用户个人中心
│   │   │   └── retention.html
│   │   ├── image/ (upload/add/extract/process)
│   │   ├── audio/ (upload/add/extract/process)
│   │   ├── video/ (upload/add/extract/process)
│   │   └── text/  (upload/add/extract/process)
│   ├── static/                       # 静态资源
│   │   ├── css/ (custom.css, bootstrap.min.css, 等)
│   │   └── js/  (common.js, bootstrap.bundle.min.js, 等)
│   └── utils/                        # 工具与算法封装
│       ├── configs                   # 视频水印算法模型配置文件夹
│       ├── videoseal                 # 视频水印算法模型使用工具文件夹
│       ├── src                       # 音频水印算法模型使用工具文件夹
│       ├── algorithm_selector.py     # 按文件选择算法/提取算法
│       ├── file_config.py            # 文件类型/大小/算法配置与工具
│       ├── path_utils.py             # 用户/日期目录、临时路径、中文路径兼容与清理
│       ├── windows_compat.py         # Windows 兼容性工具
│       ├── watermark_image.py        # 图像水印
│       ├── watermark_audio.py        # 音频水印
│       ├── watermark_video.py        # 视频水印
│       └── watermark_text.py         # 文本水印
├── migrations/                       # 数据库迁移
├── instance/                         # 运行期生成文件（uploads/embeds/extracts/temp/logs）
├── requirements.txt                  # 依赖清单（固定版本）
├── README.md                         # 项目说明
├── FEEDBACK_SYSTEM.md                # 反馈系统说明
├── ckpts                             # 视频水印算法模型文件
├── clean_file.py                     # 负责定时清理文件
├── check_windows_compatibility.py    # Windows 兼容性检查脚本
│       ├── watermark_video.py        # 视频水印
│       └── watermark_text.py         # 文本水印
├── migrations/                       # 数据库迁移
├── instance/                         # 运行期生成文件（uploads/embeds/extracts/temp/logs）
├── requirements.txt                  # 依赖清单（固定版本）
├── README.md                         # 项目说明
├── ckpts                             # 视频水印算法模型文件
├── clean_file                        # 负责定时清理文件
└── README_ALGORITHM.md               # 算法扩展说明
```

## 配置说明

### 环境变量

Java 与 Worker 的键名见 **`backend-java/deploy/watermark-api.env.example`** 与 **`backend-java/deploy/watermark-worker.env.example`**。常见项包括：

- **`WM_DATASOURCE_URL`** / **`SQLALCHEMY_DATABASE_URI`**：MySQL 连接（Java 与 Python 键名不同）
- **`WM_INSTANCE_PATH`** / **`INSTANCE_PATH`**：本机实例目录
- **`MAX_CONTENT_LENGTH`**（若仍在部分脚本中使用）：最大上传大小

### 文件大小限制

- 图片文件：50MB
- 音频文件：50MB
- 视频文件：500MB

## 清理脚本（需要在服务器提前挂载后台）

提供 `clean_file.py` 脚本用于定期清理过期文件/临时文件。

示例：

```bash
# 只执行一次，清理默认目录（uploads/embeds/extracts/temp）中7天前的文件
python clean_file.py

# 指定目录并 dry-run
python clean_file.py -p instance/temp --dry-run

# 每10分钟循环扫描，并清理空目录
python clean_file.py -i 600 --prune-empty

# 指定过期天数为30天
python clean_file.py -d 30

# 建议采用以下命令运行在服务器上
# 先试运行，确保不会误删
nohup python3 cleaner.py -d 7 -i 3000 --dry-run > cleaner.log 2>&1 &

# 确认输出无误后，去掉 --dry-run 真删
nohup python3 cleaner.py -d 7 -i 3000 > cleaner.log 2>&1 &

```

## 算法扩展

本项目支持水印算法的模块化扩展，详细的算法集成指南请参考 [README_ALGORITHM.md](README_ALGORITHM.md)。主要特点包括：

- **标准接口**: 提供统一的算法接口规范
- **自动集成**: 通过配置文件自动加载新算法
- **独立开发**: 支持算法的独立开发和测试
- **文档完备**: 提供详细的开发指南和示例

FLASK_ENV=development
FLASK_DEBUG=1
FLASK_APP=watermark
SECRET_KEY=your_secret_key_here
SQLALCHEMY_DATABASE_URI=mysql+pymysql://root:123456@localhost:3306/uestcwm
SQLALCHEMY_TRACK_MODIFICATIONS=False

# 基础路径配置
INSTANCE_PATH=instance
TEMP_FOLDER=instance/temp
LOGS_FOLDER=instance/logs
# 按媒体类型分类的存储路径
# 图片文件路径
IMAGE_UPLOAD_FOLDER=instance/uploads/images
IMAGE_EXTRACT_FOLDER=instance/extracts/images  
IMAGE_EMBED_FOLDER=instance/embeds/images

# 音频文件路径
AUDIO_UPLOAD_FOLDER=instance/uploads/audio
AUDIO_EXTRACT_FOLDER=instance/extracts/audio
AUDIO_EMBED_FOLDER=instance/embeds/audio

# 视频文件路径
VIDEO_UPLOAD_FOLDER=instance/uploads/video
VIDEO_EXTRACT_FOLDER=instance/extracts/video
VIDEO_EMBED_FOLDER=instance/embeds/video

# 文档文件路径
TEXT_UPLOAD_FOLDER=instance/uploads/documents
TEXT_EXTRACT_FOLDER=instance/extracts/documents
TEXT_EMBED_FOLDER=instance/embeds/documents

# 不同文件类型的大小限制 (字节)
# 图片文件：500MB
IMAGE_MAX_SIZE=524288000
# 音频文件：500MB  
AUDIO_MAX_SIZE=524288000
# 视频文件：2GB
VIDEO_MAX_SIZE=2147483648
# 文档文件：100MB
TEXT_MAX_SIZE=104857600

# 默认文件大小限制
DEFAULT_MAX_SIZE=104857600

# 日志配置
LOG_LEVEL=INFO
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5

# 统一时间配置
# 共用时间 API（返回 UTC）。示例：worldtimeapi；也可指向你们的内部网关。
COMMON_TIME_API_URL=https://worldtimeapi.org/api/timezone/Etc/UTC
# 展示时区（IANA 标准名称），默认 Asia/Shanghai，可改如 Europe/Berlin、UTC 等
APP_TIMEZONE=Asia/shanghai


from watermark.utils import watermark_image, watermark_video, watermark_audio

modules = {
    "image": watermark_image,
    "video": watermark_video,
    "audio": watermark_audio
}

def watermarks_select(media_type, operation, input_file, watermark=""):
    """
    动态调用 watermark_image.embed / watermark_image.extract /
               watermark_video.embed / ...
    """
    # 1. 验证类型
    if media_type not in modules:
        raise ValueError(f"Unsupported media_type: {media_type!r}, must be one of {list(modules)}")

    mod = modules[media_type]

    # 2. 验证操作
    if operation not in ("embed", "extract"):
        raise ValueError(f"Unsupported operation: {operation!r}, must be 'embed' or 'extract'")

    # 3. 取函数并调用
    func = getattr(mod, operation)
    # 取mod表示的对象中的operation对应的函数并调用
    if operation == "embed":
        return func(input_file, watermark)
    else:
        return func(input_file)
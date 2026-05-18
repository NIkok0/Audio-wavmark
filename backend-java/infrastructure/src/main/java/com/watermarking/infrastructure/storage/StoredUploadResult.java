package com.watermarking.infrastructure.storage;

/**
 * 本地落盘结果（与 Flask {@code handle_file_upload} 返回的 file_info 对应）。
 */
public record StoredUploadResult(
        String absolutePath,
        long sizeBytes,
        String sha256Hex,
        String mimeType,
        String fileFormat,
        String storedFilename) {}

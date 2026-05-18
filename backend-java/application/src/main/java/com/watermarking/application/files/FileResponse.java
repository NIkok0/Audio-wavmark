package com.watermarking.application.files;

import com.watermarking.domain.model.File;

import java.time.Instant;

/**
 * 对外文件 DTO，字段与 {@link File} 实体对齐（含路径，便于内网部署与排障；公网暴露时可再收敛）。
 */
public record FileResponse(
        Integer id,
        Integer uploaderId,
        Integer groupId,
        String filename,
        String originalPath,
        String watermarkedPath,
        String fileHash,
        String fileWatermarkHash,
        boolean hasWatermark,
        String fileType,
        String fileFormat,
        long fileSize,
        String mimeType,
        String watermarkType,
        String watermarkText,
        String originalWatermarkText,
        String watermarkSeed,
        String processingStatus,
        String errorMessage,
        Instant createdAt,
        Instant updatedAt) {

    public static FileResponse fromEntity(File f) {
        return new FileResponse(
                f.getId(),
                f.getUploader() != null ? f.getUploader().getId() : null,
                f.getGroup() != null ? f.getGroup().getId() : null,
                f.getFilename(),
                f.getOriginalPath(),
                f.getWatermarkedPath(),
                f.getFileHash(),
                f.getFileWatermarkHash(),
                f.isHasWatermark(),
                f.getFileType(),
                f.getFileFormat(),
                f.getFileSize(),
                f.getMimeType(),
                f.getWatermarkType(),
                f.getWatermarkText(),
                f.getOriginalWatermarkText(),
                f.getWatermarkSeed(),
                f.getProcessingStatus(),
                f.getErrorMessage(),
                f.getCreatedAt(),
                f.getUpdatedAt());
    }
}

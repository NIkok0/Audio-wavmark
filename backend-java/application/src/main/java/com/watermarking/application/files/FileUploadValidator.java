package com.watermarking.application.files;

import org.springframework.stereotype.Component;

import java.util.Locale;
import java.util.Map;
import java.util.Set;

/**
 * 扩展名 / 媒体类型校验，对齐 {@code watermark/utils/file_config.py} 中各类型扩展集合。
 */
@Component
public class FileUploadValidator {

    private static final Map<String, Set<String>> EXTENSIONS_BY_MEDIA = Map.of(
            "image", Set.of("jpg", "jpeg", "png", "bmp"),
            "video", Set.of("mp4", "avi", "mov"),
            "audio", Set.of("ogg", "mp3", "wav", "flac", "m4a", "aac"),
            "text",
                    Set.of("txt", "doc", "docx", "xlsx", "xml", "xls", "pdf", "md", "sql", "csv"));

    public void validateMediaType(String mediaType) {
        if (mediaType == null || !EXTENSIONS_BY_MEDIA.containsKey(mediaType)) {
            throw new InvalidFileUploadException("不支持的媒体类型，应为 image / audio / video / text");
        }
    }

    public void validateExtensionForMedia(String mediaType, String extensionLowerCaseNoDot) {
        validateMediaType(mediaType);
        String ext = extensionLowerCaseNoDot == null ? "" : extensionLowerCaseNoDot.toLowerCase(Locale.ROOT);
        if (!EXTENSIONS_BY_MEDIA.get(mediaType).contains(ext)) {
            throw new InvalidFileUploadException("不支持的文件类型: " + ext);
        }
    }

    public String extensionFromFilename(String filename) {
        if (filename == null) {
            return "";
        }
        int dot = filename.lastIndexOf('.');
        if (dot < 0 || dot == filename.length() - 1) {
            return "";
        }
        return filename.substring(dot + 1).toLowerCase(Locale.ROOT);
    }
}

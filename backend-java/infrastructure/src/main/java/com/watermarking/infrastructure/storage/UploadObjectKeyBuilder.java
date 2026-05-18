package com.watermarking.infrastructure.storage;

import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.UUID;

/**
 * 生成直传对象键：{@code wm/{userId}/{mediaSegment}/{yyyyMMdd}/{uuid}_{filename}}，与本地目录语义对应。
 */
public final class UploadObjectKeyBuilder {

    private static final DateTimeFormatter DAY = DateTimeFormatter.ofPattern("yyyyMMdd").withZone(ZoneOffset.UTC);

    private UploadObjectKeyBuilder() {}

    public static String mediaSegment(String mediaType) {
        return switch (mediaType) {
            case "image" -> "images";
            case "audio" -> "audio";
            case "video" -> "video";
            case "text" -> "documents";
            default -> throw new IllegalArgumentException("不支持的媒体类型: " + mediaType);
        };
    }

    public static String directoryPrefix(int userId, String mediaType) {
        String day = DAY.format(Instant.now());
        return "wm/" + userId + "/" + mediaSegment(mediaType) + "/" + day + "/";
    }

    public static String build(int userId, String mediaType, String securedFilename) {
        String id = UUID.randomUUID().toString();
        return directoryPrefix(userId, mediaType) + id + "_" + securedFilename;
    }

    public static boolean isAllowedForUser(int userId, String objectKey) {
        if (objectKey == null || objectKey.isBlank()) {
            return false;
        }
        String prefix = "wm/" + userId + "/";
        return objectKey.startsWith(prefix) && !objectKey.contains("..");
    }
}

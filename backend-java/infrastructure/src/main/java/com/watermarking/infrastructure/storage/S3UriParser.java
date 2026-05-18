package com.watermarking.infrastructure.storage;

import java.net.URI;
import java.util.Optional;

/**
 * 解析 {@code s3://bucket/key} 形态路径（与 {@code FileService} 登记的对象路径一致）。
 */
public final class S3UriParser {

    private S3UriParser() {}

    public record Parsed(String bucket, String key) {}

    public static Optional<Parsed> tryParse(String uri) {
        if (uri == null || uri.isBlank()) {
            return Optional.empty();
        }
        try {
            URI u = URI.create(uri.trim());
            if (!"s3".equalsIgnoreCase(u.getScheme())) {
                return Optional.empty();
            }
            String bucket = u.getHost();
            if (bucket == null || bucket.isBlank()) {
                return Optional.empty();
            }
            String path = u.getPath();
            if (path == null || path.isEmpty() || "/".equals(path)) {
                return Optional.empty();
            }
            String key = path.startsWith("/") ? path.substring(1) : path;
            return Optional.of(new Parsed(bucket, key));
        } catch (IllegalArgumentException e) {
            return Optional.empty();
        }
    }
}

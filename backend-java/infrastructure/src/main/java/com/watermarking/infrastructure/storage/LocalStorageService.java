package com.watermarking.infrastructure.storage;

import org.springframework.stereotype.Service;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.DigestInputStream;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.HexFormat;

/**
 * 本地存储：目录布局对齐 Flask {@code MEDIA_FOLDERS} + {@code path_utils#get_user_dated_upload_dir}
 *（{@code upload/<媒体>/用户�?yyyyMMdd/yyyyMMdd_HHmmss_文件名}）�?
 */
@Service
public class LocalStorageService {

    private static final DateTimeFormatter DAY = DateTimeFormatter.ofPattern("yyyyMMdd").withZone(ZoneOffset.UTC);
    private static final DateTimeFormatter STAMP =
            DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss").withZone(ZoneOffset.UTC);

    private final WmStorageProperties properties;
    private final Path instanceRootAbsolute;

    public LocalStorageService(WmStorageProperties properties) {
        this.properties = properties;
        try {
            this.instanceRootAbsolute = Path.of(properties.getInstancePath()).toAbsolutePath().normalize();
            Files.createDirectories(instanceRootAbsolute);
            ensureMediaDirectories();
        } catch (IOException e) {
            throw new UncheckedIOException("无法创建实例目录: " + properties.getInstancePath(), e);
        }
    }

    /** �?Flask {@code ensure_directories()} �?uploads/extracts/embeds 子目录一致�?*/
    private void ensureMediaDirectories() throws IOException {
        for (String media : new String[] {"images", "audio", "video", "documents"}) {
            Files.createDirectories(instanceRootAbsolute.resolve(Path.of("uploads", media)));
            Files.createDirectories(instanceRootAbsolute.resolve(Path.of("extracts", media)));
            Files.createDirectories(instanceRootAbsolute.resolve(Path.of("embeds", media)));
        }
        Files.createDirectories(instanceRootAbsolute.resolve("temp"));
        Files.createDirectories(instanceRootAbsolute.resolve("logs"));
    }

    public Path getInstanceRootAbsolute() {
        return instanceRootAbsolute;
    }

    /**
     * �?Flask {@code get_media_folder(mediaType, 'upload')} 下再拼用�?日期目录一致�?
     */
    public StoredUploadResult saveUpload(
            String mediaType,
            String username,
            String originalClientFilename,
            InputStream inputStream,
            long declaredSizeBytes)
            throws IOException {
        String uploadSegment = uploadSegmentFor(mediaType);
        String userDir = secureUsername(username);
        String day = DAY.format(Instant.now());
        String stamp = STAMP.format(Instant.now());
        String safeName = secureFilename(originalClientFilename);
        String uniqueName = stamp + "_" + safeName;

        Path dir = instanceRootAbsolute.resolve(Path.of("uploads", uploadSegment, userDir, day));
        Files.createDirectories(dir);
        Path target = dir.resolve(uniqueName);

        MessageDigest digest;
        try {
            digest = MessageDigest.getInstance("SHA-256");
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException(e);
        }
        long max = properties.maxBytesForMediaType(mediaType);
        if (declaredSizeBytes > 0 && declaredSizeBytes > max) {
            throw new IllegalArgumentException("文件大小超过限制");
        }
        try (DigestInputStream dis = new DigestInputStream(inputStream, digest);
                OutputStream out = Files.newOutputStream(target)) {
            byte[] buf = new byte[8192];
            long written = 0;
            int n;
            while ((n = dis.read(buf)) >= 0) {
                written += n;
                if (written > max) {
                    Files.deleteIfExists(target);
                    throw new IllegalArgumentException("文件大小超过限制");
                }
                out.write(buf, 0, n);
            }
            String sha = HexFormat.of().formatHex(digest.digest());
            String ext = extensionOf(safeName);
            String mime = guessMime(ext);
            return new StoredUploadResult(target.toAbsolutePath().normalize().toString(), written, sha, mime, ext, uniqueName);
        }
    }

    public void deleteIfExists(String absoluteOrRelativePath) throws IOException {
        if (absoluteOrRelativePath == null || absoluteOrRelativePath.isBlank()) {
            return;
        }
        Path p = Path.of(absoluteOrRelativePath).toAbsolutePath().normalize();
        assertUnderInstanceRoot(p);
        Files.deleteIfExists(p);
    }

    public Path resolveReadablePath(String storedPath) throws IOException {
        if (storedPath == null || storedPath.isBlank()) {
            throw new IllegalArgumentException("路径为空");
        }
        Path p = Path.of(storedPath).toAbsolutePath().normalize();
        assertUnderInstanceRoot(p);
        if (!Files.isRegularFile(p)) {
            throw new java.nio.file.NoSuchFileException(p.toString());
        }
        return p;
    }

    private void assertUnderInstanceRoot(Path p) throws IOException {
        Path base = instanceRootAbsolute.toRealPath();
        Path cand = p.toAbsolutePath().normalize();
        if (!cand.startsWith(base)) {
            throw new SecurityException("\u8def\u5f84\u4e0d\u5728\u5b9e\u4f8b\u76ee\u5f55\u5185");
        }
    }

    private static String uploadSegmentFor(String mediaType) {
        return switch (mediaType) {
            case "image" -> "images";
            case "audio" -> "audio";
            case "video" -> "video";
            case "text" -> "documents";
            default -> throw new IllegalArgumentException("不支持的媒体类型: " + mediaType);
        };
    }

    /**
     * 对齐 {@code path_utils._secure_filename_with_chinese(username)}�?
     */
    public static String secureUsername(String username) {
        if (username == null || username.isBlank()) {
            return "anonymous";
        }
        String s = username.replaceAll("[^\\u4e00-\\u9fa5A-Za-z0-9_.\\-]", "_");
        s = s.replaceAll("^[._]+|[._]+$", "");
        return s.isEmpty() ? "anonymous" : s;
    }

    /**
     * 对齐 {@code views.secure_filename_with_chinese} 思路（保留中文、字母数字与常见符号）�?
     */
    public static String secureFilename(String filename) {
        if (filename == null || filename.isBlank()) {
            return "_anonymous";
        }
        int dot = filename.lastIndexOf('.');
        String ext = dot > 0 && dot < filename.length() - 1 ? filename.substring(dot) : "";
        String namePart = dot > 0 ? filename.substring(0, dot) : filename;
        String base = namePart.replaceAll("[^\\w\\u4e00-\\u9fff]+", "_");
        if (base.isBlank() || base.equals("_")) {
            return ext.isEmpty() ? "_anonymous" : "_anonymous" + ext;
        }
        return base + ext;
    }
    private static String extensionOf(String filename) {
        int dot = filename.lastIndexOf('.');
        if (dot < 0 || dot == filename.length() - 1) {
            return "";
        }
        return filename.substring(dot + 1).toLowerCase();
    }

    /** �?{@code file_config.get_mime_type} 常用项对齐；未知�?application/octet-stream */
    public static String guessMime(String ext) {
        return switch (ext) {
            case "jpg", "jpeg" -> "image/jpeg";
            case "png" -> "image/png";
            case "bmp" -> "image/bmp";
            case "mp4" -> "video/mp4";
            case "avi" -> "video/avi";
            case "mov" -> "video/quicktime";
            case "ogg" -> "audio/ogg";
            case "mp3" -> "audio/mpeg";
            case "wav" -> "audio/wav";
            case "flac" -> "audio/flac";
            case "m4a" -> "audio/m4a";
            case "aac" -> "audio/aac";
            case "txt" -> "text/plain";
            case "doc" -> "application/msword";
            case "docx" -> "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
            case "xlsx" -> "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
            case "xml" -> "application/xml";
            case "xls" -> "application/vnd.ms-excel";
            case "pdf" -> "application/pdf";
            case "md" -> "text/markdown";
            case "sql" -> "application/sql";
            case "csv" -> "text/csv";
            default -> "application/octet-stream";
        };
    }
}

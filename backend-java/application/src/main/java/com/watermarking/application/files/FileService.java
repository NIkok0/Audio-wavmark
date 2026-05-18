package com.watermarking.application.files;

import com.watermarking.domain.model.File;
import com.watermarking.infrastructure.persistence.FileRepository;
import com.watermarking.infrastructure.persistence.UserRepository;
import com.watermarking.infrastructure.storage.LocalStorageService;
import com.watermarking.infrastructure.storage.S3ObjectStorageService;
import com.watermarking.infrastructure.storage.Sha256Util;
import com.watermarking.infrastructure.storage.StoredUploadResult;
import com.watermarking.infrastructure.storage.ObjectStorageUnavailableException;
import com.watermarking.infrastructure.storage.UploadObjectKeyBuilder;
import com.watermarking.infrastructure.storage.WmStorageProperties;
import io.micrometer.core.instrument.MeterRegistry;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import software.amazon.awssdk.services.s3.model.HeadObjectResponse;

import java.io.IOException;
import java.io.InputStream;
import java.net.URI;
import java.nio.file.NoSuchFileException;
import java.nio.file.Path;

@Service
public class FileService {

    private final FileRepository fileRepository;
    private final UserRepository userRepository;
    private final LocalStorageService localStorageService;
    private final FileUploadValidator uploadValidator;
    private final S3ObjectStorageService s3ObjectStorageService;
    private final WmStorageProperties storageProperties;
    private final MeterRegistry meterRegistry;

    public FileService(
            FileRepository fileRepository,
            UserRepository userRepository,
            LocalStorageService localStorageService,
            FileUploadValidator uploadValidator,
            S3ObjectStorageService s3ObjectStorageService,
            WmStorageProperties storageProperties,
            MeterRegistry meterRegistry) {
        this.fileRepository = fileRepository;
        this.userRepository = userRepository;
        this.localStorageService = localStorageService;
        this.uploadValidator = uploadValidator;
        this.s3ObjectStorageService = s3ObjectStorageService;
        this.storageProperties = storageProperties;
        this.meterRegistry = meterRegistry;
    }

    @Transactional(readOnly = true)
    public PagedFilesResponse listForUploader(Integer uploaderId, String fileType, String filenameQuery, int page, int size) {
        int p = Math.max(0, page);
        int s = Math.min(100, Math.max(1, size));
        PageRequest pr = PageRequest.of(p, s, Sort.by(Sort.Direction.DESC, "createdAt"));
        Page<File> result;
        boolean hasQ = filenameQuery != null && !filenameQuery.isBlank();
        if (hasQ) {
            String q = filenameQuery.trim();
            result = fileRepository.findByUploader_IdAndFilenameContainingIgnoreCaseOrderByCreatedAtDesc(uploaderId, q, pr);
        } else if (fileType == null || fileType.isBlank()) {
            result = fileRepository.findByUploader_IdOrderByCreatedAtDesc(uploaderId, pr);
        } else {
            result = fileRepository.findByUploader_IdAndFileTypeOrderByCreatedAtDesc(uploaderId, fileType, pr);
        }
        return new PagedFilesResponse(
                result.getContent().stream().map(FileResponse::fromEntity).toList(),
                result.getTotalElements(),
                result.getNumber(),
                result.getSize());
    }

    @Transactional(readOnly = true)
    public FileResponse getForUploader(Integer uploaderId, Integer fileId) {
        File f =
                fileRepository.findByIdAndUploader_Id(fileId, uploaderId).orElseThrow(() -> new StoredFileNotFoundException("文件不存在"));
        return FileResponse.fromEntity(f);
    }

    @Transactional
    public FileResponse upload(
            Integer uploaderId, String username, String mediaType, String clientOriginalFilename, InputStream in, long declaredSize)
            throws IOException {
        uploadValidator.validateMediaType(mediaType);
        if (clientOriginalFilename == null || clientOriginalFilename.isBlank()) {
            throw new InvalidFileUploadException("没有选择文件");
        }
        String secured = LocalStorageService.secureFilename(clientOriginalFilename);
        String ext = uploadValidator.extensionFromFilename(secured);
        if (ext.isEmpty()) {
            throw new InvalidFileUploadException("文件缺少扩展名");
        }
        uploadValidator.validateExtensionForMedia(mediaType, ext);

        StoredUploadResult stored =
                localStorageService.saveUpload(mediaType, username, clientOriginalFilename, in, declaredSize);

        File entity = new File();
        entity.setFilename(secured);
        entity.setOriginalPath(stored.absolutePath());
        entity.setFileHash(stored.sha256Hex());
        entity.setFileType(mediaType);
        entity.setFileFormat(stored.fileFormat());
        entity.setFileSize(stored.sizeBytes());
        entity.setMimeType(stored.mimeType());
        entity.setProcessingStatus("pending");
        entity.setHasWatermark(false);
        entity.setUploader(userRepository.getReferenceById(uploaderId));

        File saved = fileRepository.save(entity);
        return FileResponse.fromEntity(saved);
    }

    /**
     * 直传完成后登记元数据：Head 校验 ETag/Size，流式计算 SHA256（上限见 {@code wm.storage.max-hash-bytes}），
     * {@code original_path} 使用 {@code s3://bucket/key} 便于阶段 4 Worker 与删除逻辑统一处理。
     */
    @Transactional
    public FileResponse completeObjectUpload(int userId, CompleteUploadCommand cmd) throws IOException {
        try {
            if (!UploadObjectKeyBuilder.isAllowedForUser(userId, cmd.objectKey())) {
                throw new FileAccessDeniedException("objectKey 与当前用户不匹配");
            }
            uploadValidator.validateMediaType(cmd.mediaType());
            String secured = LocalStorageService.secureFilename(cmd.filename());
            String ext = uploadValidator.extensionFromFilename(secured);
            if (ext.isEmpty()) {
                throw new InvalidFileUploadException("文件缺少扩展名");
            }
            uploadValidator.validateExtensionForMedia(cmd.mediaType(), ext);

            if (!s3ObjectStorageService.isEnabled()) {
                throw new ObjectStorageUnavailableException("对象存储未启用，无法完成直传登记");
            }

            HeadObjectResponse head = s3ObjectStorageService.head(cmd.objectKey());
            long contentLength = head.contentLength();
            if (contentLength != cmd.size()) {
                throw new InvalidFileUploadException("大小与对象元数据不一致");
            }
            String headEtag = normalizeEtag(head.eTag());
            String clientEtag = normalizeEtag(cmd.etag());
            if (!headEtag.equalsIgnoreCase(clientEtag)) {
                throw new InvalidFileUploadException("ETag 与对象元数据不一致");
            }

            long maxHash =
                    Math.min(storageProperties.getMaxHashBytes(), storageProperties.maxBytesForMediaType(cmd.mediaType()));
            if (contentLength > maxHash) {
                throw new InvalidFileUploadException("对象过大，超过服务端哈希上限");
            }

            String shaHex;
            try (InputStream in = s3ObjectStorageService.openObjectStream(cmd.objectKey())) {
                shaHex = Sha256Util.sha256Hex(in, contentLength);
            }

            String bucket = s3ObjectStorageService.getBucket();
            String uri = "s3://" + bucket + "/" + cmd.objectKey();

            String mime = head.contentType() != null && !head.contentType().isBlank()
                    ? head.contentType()
                    : LocalStorageService.guessMime(ext);

            File entity = new File();
            entity.setFilename(secured);
            entity.setOriginalPath(uri);
            entity.setFileHash(shaHex);
            entity.setFileType(cmd.mediaType());
            entity.setFileFormat(ext);
            entity.setFileSize(contentLength);
            entity.setMimeType(mime);
            entity.setProcessingStatus("pending");
            entity.setHasWatermark(false);
            entity.setUploader(userRepository.getReferenceById(userId));

            File saved = fileRepository.save(entity);
            meterRegistry.counter("wm.files.s3_complete", "result", "success").increment();
            return FileResponse.fromEntity(saved);
        } catch (IOException e) {
            meterRegistry.counter("wm.files.s3_complete", "result", "failure").increment();
            throw e;
        } catch (RuntimeException e) {
            meterRegistry.counter("wm.files.s3_complete", "result", "failure").increment();
            throw e;
        }
    }

    @Transactional
    public void deleteForUploader(Integer uploaderId, Integer fileId) throws IOException {
        File f =
                fileRepository.findByIdAndUploader_Id(fileId, uploaderId).orElseThrow(() -> new StoredFileNotFoundException("文件不存在"));
        deleteFileRowAndStorage(f);
    }

    /**
     * 保留期清理等系统任务：不按上传者会话校验，仅按主键删除元数据与对象/本机文件。
     */
    @Transactional
    public void deleteByIdForSystemRetention(Integer fileId) throws IOException {
        File f = fileRepository.findById(fileId).orElse(null);
        if (f == null) {
            return;
        }
        deleteFileRowAndStorage(f);
    }

    private void deleteFileRowAndStorage(File f) throws IOException {
        String originalPath = f.getOriginalPath();
        String watermarkedPath = f.getWatermarkedPath();
        boolean watermarked = f.isHasWatermark();

        fileRepository.delete(f);

        if (watermarked) {
            deletePhysical(watermarkedPath);
        } else {
            deletePhysical(originalPath);
        }
    }

    private void deletePhysical(String path) throws IOException {
        if (path == null || path.isBlank()) {
            return;
        }
        if (path.startsWith("s3://")) {
            ParsedS3 loc = parseS3Uri(path);
            if (loc == null) {
                return;
            }
            if (!s3ObjectStorageService.isEnabled()) {
                return;
            }
            if (!loc.bucket().equals(s3ObjectStorageService.getBucket())) {
                throw new SecurityException("非法的对象存储路径");
            }
            s3ObjectStorageService.deleteObject(loc.key());
        } else {
            localStorageService.deleteIfExists(path);
        }
    }

    @Transactional(readOnly = true)
    public LoadedContent loadContentForUploader(Integer uploaderId, Integer fileId) throws IOException {
        File f =
                fileRepository.findByIdAndUploader_Id(fileId, uploaderId).orElseThrow(() -> new StoredFileNotFoundException("文件不存在"));
        String target = f.getWatermarkedPath() != null && !f.getWatermarkedPath().isBlank()
                ? f.getWatermarkedPath()
                : f.getOriginalPath();
        if (target == null || target.isBlank()) {
            throw new StoredFileNotFoundException("未找到可下载的文件路径");
        }
        if (target.startsWith("s3://")) {
            ParsedS3 loc = parseS3Uri(target);
            if (loc == null) {
                throw new StoredFileNotFoundException("无效的对象路径");
            }
            if (!s3ObjectStorageService.isEnabled()) {
                throw new ObjectStorageUnavailableException("对象存储未启用");
            }
            if (!loc.bucket().equals(s3ObjectStorageService.getBucket())) {
                throw new FileAccessDeniedException("无权访问该对象");
            }
            if (!UploadObjectKeyBuilder.isAllowedForUser(uploaderId, loc.key())) {
                throw new FileAccessDeniedException("无权访问该对象");
            }
            String url = s3ObjectStorageService.presignGet(loc.key());
            return LoadedContent.redirect(url, f.getFilename(), f.getMimeType());
        }
        try {
            Path path = localStorageService.resolveReadablePath(target);
            Resource resource = new FileSystemResource(path);
            return LoadedContent.local(resource, f.getFilename(), f.getMimeType());
        } catch (NoSuchFileException e) {
            throw new StoredFileNotFoundException("文件不存在或已被移除");
        } catch (SecurityException e) {
            throw new FileAccessDeniedException("无权访问该文件路径");
        }
    }

    private record ParsedS3(String bucket, String key) {}

    private static ParsedS3 parseS3Uri(String uri) {
        try {
            URI u = URI.create(uri);
            if (!"s3".equalsIgnoreCase(u.getScheme())) {
                return null;
            }
            String bucket = u.getHost();
            if (bucket == null || bucket.isBlank()) {
                return null;
            }
            String path = u.getPath();
            if (path == null || path.isEmpty() || "/".equals(path)) {
                return null;
            }
            String key = path.startsWith("/") ? path.substring(1) : path;
            return new ParsedS3(bucket, key);
        } catch (IllegalArgumentException e) {
            return null;
        }
    }

    private static String normalizeEtag(String raw) {
        if (raw == null) {
            return "";
        }
        String s = raw.trim();
        if (s.startsWith("\"") && s.endsWith("\"") && s.length() >= 2) {
            s = s.substring(1, s.length() - 1);
        }
        return s;
    }

    public record LoadedContent(Resource resource, String downloadFilename, String mimeType, String redirectUrl) {

        public static LoadedContent local(Resource resource, String downloadFilename, String mimeType) {
            return new LoadedContent(resource, downloadFilename, mimeType, null);
        }

        public static LoadedContent redirect(String redirectUrl, String downloadFilename, String mimeType) {
            return new LoadedContent(null, downloadFilename, mimeType, redirectUrl);
        }

        public boolean redirect() {
            return redirectUrl != null && !redirectUrl.isBlank();
        }
    }
}

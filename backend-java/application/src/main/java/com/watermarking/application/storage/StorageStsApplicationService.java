package com.watermarking.application.storage;

import com.watermarking.application.files.FileUploadValidator;
import com.watermarking.infrastructure.storage.CosFederationTokenIssuer;
import com.watermarking.infrastructure.storage.LocalStorageService;
import com.watermarking.infrastructure.storage.S3ObjectStorageService;
import com.watermarking.infrastructure.storage.UploadObjectKeyBuilder;
import com.watermarking.infrastructure.storage.ObjectStorageUnavailableException;
import com.watermarking.infrastructure.storage.WmStorageProperties;
import com.tencentcloudapi.common.exception.TencentCloudSDKException;
import jakarta.validation.constraints.NotBlank;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.Locale;

@Service
public class StorageStsApplicationService {

    private final WmStorageProperties properties;
    private final S3ObjectStorageService s3ObjectStorageService;
    private final CosFederationTokenIssuer cosFederationTokenIssuer;
    private final FileUploadValidator uploadValidator;

    public StorageStsApplicationService(
            WmStorageProperties properties,
            S3ObjectStorageService s3ObjectStorageService,
            CosFederationTokenIssuer cosFederationTokenIssuer,
            FileUploadValidator uploadValidator) {
        this.properties = properties;
        this.s3ObjectStorageService = s3ObjectStorageService;
        this.cosFederationTokenIssuer = cosFederationTokenIssuer;
        this.uploadValidator = uploadValidator;
    }

    public StsIssueResponse issue(StsIssueRequest request, int userId) throws TencentCloudSDKException {
        uploadValidator.validateMediaType(request.mediaType());
        String secured = LocalStorageService.secureFilename(request.filename());
        String ext = uploadValidator.extensionFromFilename(secured);
        if (ext.isEmpty()) {
            throw new IllegalArgumentException("文件缺少扩展名");
        }
        uploadValidator.validateExtensionForMedia(request.mediaType(), ext);

        String objectKey = UploadObjectKeyBuilder.build(userId, request.mediaType(), secured);
        String backend = properties.getBackend() == null ? "minio" : properties.getBackend().toLowerCase(Locale.ROOT);

        if ("cos".equals(backend)) {
            String dirPrefix = UploadObjectKeyBuilder.directoryPrefix(userId, request.mediaType());
            CosFederationTokenIssuer.CosStsCredentials c = cosFederationTokenIssuer.issue(userId, dirPrefix);
            long exp = c.expiredTime();
            return new StsIssueResponse(
                    "cos",
                    c.bucket(),
                    c.region(),
                    objectKey,
                    null,
                    exp,
                    c.tmpSecretId(),
                    c.tmpSecretKey(),
                    c.sessionToken());
        }

        if (!s3ObjectStorageService.isEnabled()) {
            throw new ObjectStorageUnavailableException("MinIO/S3 未配置：请设置 wm.storage.minio.endpoint 与密钥");
        }
        String putUrl = s3ObjectStorageService.presignPut(objectKey);
        long exp = Instant.now().plus(properties.getPresignPutTtl()).getEpochSecond();
        WmStorageProperties.Minio m = properties.getMinio();
        return new StsIssueResponse(
                "minio",
                s3ObjectStorageService.getBucket(),
                m.getRegion(),
                objectKey,
                putUrl,
                exp,
                null,
                null,
                null);
    }

    public record StsIssueRequest(@NotBlank String mediaType, @NotBlank String filename) {}

    public record StsIssueResponse(
            String backend,
            String bucket,
            String region,
            String objectKey,
            String putUrl,
            long credentialsExpireAtEpochSeconds,
            String tmpSecretId,
            String tmpSecretKey,
            String sessionToken) {}
}

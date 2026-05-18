package com.watermarking.infrastructure.storage;

import io.micrometer.core.instrument.MeterRegistry;
import jakarta.annotation.PostConstruct;
import org.springframework.stereotype.Service;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.core.ResponseInputStream;
import software.amazon.awssdk.http.urlconnection.UrlConnectionHttpClient;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.S3Configuration;
import software.amazon.awssdk.services.s3.model.CreateBucketRequest;
import software.amazon.awssdk.services.s3.model.DeleteObjectRequest;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;
import software.amazon.awssdk.services.s3.model.GetObjectResponse;
import software.amazon.awssdk.services.s3.model.HeadObjectRequest;
import software.amazon.awssdk.services.s3.model.HeadObjectResponse;
import software.amazon.awssdk.services.s3.model.NoSuchKeyException;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;
import software.amazon.awssdk.services.s3.model.S3Exception;
import software.amazon.awssdk.services.s3.presigner.S3Presigner;
import software.amazon.awssdk.services.s3.presigner.model.GetObjectPresignRequest;
import software.amazon.awssdk.services.s3.presigner.model.PutObjectPresignRequest;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.URI;
import java.util.Locale;

/**
 * S3 兼容客户端（MinIO 开发 / COS S3 兼容域名），进程内单例；与《选型》COS 单例要求一致。
 */
@Service
public class S3ObjectStorageService {

    private final WmStorageProperties properties;
    private final MeterRegistry meterRegistry;
    private S3Client s3Client;
    private S3Presigner presigner;
    private String bucket;
    private boolean enabled;

    public S3ObjectStorageService(WmStorageProperties properties, MeterRegistry meterRegistry) {
        this.properties = properties;
        this.meterRegistry = meterRegistry;
    }

    @PostConstruct
    void init() {
        String backend = properties.getBackend() == null ? "minio" : properties.getBackend().toLowerCase(Locale.ROOT);
        if ("cos".equals(backend)) {
            WmStorageProperties.Cos cos = properties.getCos();
            if (cos.getSecretId().isBlank() || cos.getSecretKey().isBlank() || cos.getBucket().isBlank()) {
                enabled = false;
                return;
            }
            this.bucket = cos.getBucket();
            URI endpoint = URI.create("https://cos." + cos.getRegion() + ".myqcloud.com");
            AwsBasicCredentials creds = AwsBasicCredentials.create(cos.getSecretId(), cos.getSecretKey());
            this.s3Client =
                    S3Client.builder()
                            .region(Region.of(cos.getRegion()))
                            .endpointOverride(endpoint)
                            .credentialsProvider(StaticCredentialsProvider.create(creds))
                            .serviceConfiguration(
                                    S3Configuration.builder().pathStyleAccessEnabled(true).chunkedEncodingEnabled(true).build())
                            .httpClient(UrlConnectionHttpClient.create())
                            .build();
            this.presigner =
                    S3Presigner.builder()
                            .region(Region.of(cos.getRegion()))
                            .endpointOverride(endpoint)
                            .credentialsProvider(StaticCredentialsProvider.create(creds))
                            .serviceConfiguration(S3Configuration.builder().pathStyleAccessEnabled(true).build())
                            .build();
            enabled = true;
        } else {
            WmStorageProperties.Minio m = properties.getMinio();
            if (m.getEndpoint() == null || m.getEndpoint().isBlank()) {
                enabled = false;
                return;
            }
            this.bucket = m.getBucket();
            URI endpoint = URI.create(m.getEndpoint());
            AwsBasicCredentials creds = AwsBasicCredentials.create(m.getAccessKey(), m.getSecretKey());
            this.s3Client =
                    S3Client.builder()
                            .region(Region.of(m.getRegion()))
                            .endpointOverride(endpoint)
                            .credentialsProvider(StaticCredentialsProvider.create(creds))
                            .serviceConfiguration(S3Configuration.builder().pathStyleAccessEnabled(true).build())
                            .httpClient(UrlConnectionHttpClient.create())
                            .build();
            this.presigner =
                    S3Presigner.builder()
                            .region(Region.of(m.getRegion()))
                            .endpointOverride(endpoint)
                            .credentialsProvider(StaticCredentialsProvider.create(creds))
                            .serviceConfiguration(S3Configuration.builder().pathStyleAccessEnabled(true).build())
                            .build();
            enabled = true;
        }
        if (!enabled) {
            return;
        }
        try {
            s3Client.createBucket(CreateBucketRequest.builder().bucket(bucket).build());
        } catch (S3Exception ignored) {
            // 桶已存在或 COS 账号无 CreateBucket 权限时忽略
        }
    }

    public boolean isEnabled() {
        return enabled;
    }

    public String getBucket() {
        return bucket;
    }

    public String presignPut(String objectKey) {
        ensureEnabled();
        PutObjectRequest put = PutObjectRequest.builder().bucket(bucket).key(objectKey).build();
        return presigner
                .presignPutObject(
                        PutObjectPresignRequest.builder()
                                .signatureDuration(properties.getPresignPutTtl())
                                .putObjectRequest(put)
                                .build())
                .url()
                .toString();
    }

    public String presignGet(String objectKey) {
        ensureEnabled();
        GetObjectRequest get = GetObjectRequest.builder().bucket(bucket).key(objectKey).build();
        return presigner
                .presignGetObject(
                        GetObjectPresignRequest.builder()
                                .signatureDuration(properties.getPresignGetTtl())
                                .getObjectRequest(get)
                                .build())
                .url()
                .toString();
    }

    public HeadObjectResponse head(String objectKey) {
        ensureEnabled();
        try {
            HeadObjectResponse r = s3Client.headObject(HeadObjectRequest.builder().bucket(bucket).key(objectKey).build());
            recordS3("head", "success", "none");
            return r;
        } catch (S3Exception e) {
            recordS3("head", "failure", errorCodeTag(e));
            throw e;
        }
    }

    public void getObjectStream(String objectKey, OutputStream out) throws IOException {
        ensureEnabled();
        try (ResponseInputStream<GetObjectResponse> in =
                s3Client.getObject(GetObjectRequest.builder().bucket(bucket).key(objectKey).build())) {
            in.transferTo(out);
            recordS3("get", "success", "none");
        } catch (NoSuchKeyException e) {
            recordS3("get", "failure", "404");
            throw new java.io.FileNotFoundException(objectKey);
        } catch (S3Exception e) {
            recordS3("get", "failure", errorCodeTag(e));
            throw e;
        }
    }

    public InputStream openObjectStream(String objectKey) {
        ensureEnabled();
        try {
            InputStream in = s3Client.getObject(GetObjectRequest.builder().bucket(bucket).key(objectKey).build());
            recordS3("get", "success", "none");
            return in;
        } catch (S3Exception e) {
            recordS3("get", "failure", errorCodeTag(e));
            throw e;
        }
    }

    public void deleteObject(String objectKey) {
        ensureEnabled();
        try {
            s3Client.deleteObject(DeleteObjectRequest.builder().bucket(bucket).key(objectKey).build());
            recordS3("delete", "success", "none");
        } catch (S3Exception e) {
            recordS3("delete", "failure", errorCodeTag(e));
            throw e;
        }
    }

    private void recordS3(String operation, String result, String errorCode) {
        meterRegistry
                .counter(
                        "wm.s3.requests",
                        "operation",
                        operation,
                        "result",
                        result,
                        "error_code",
                        errorCode)
                .increment();
    }

    private static String errorCodeTag(S3Exception e) {
        int sc = e.statusCode();
        return sc > 0 ? String.valueOf(sc) : "unknown";
    }

    private void ensureEnabled() {
        if (!enabled) {
            throw new ObjectStorageUnavailableException("对象存储未配置：请设置 wm.storage.minio.endpoint 或 wm.storage.cos 密钥与桶名");
        }
    }
}

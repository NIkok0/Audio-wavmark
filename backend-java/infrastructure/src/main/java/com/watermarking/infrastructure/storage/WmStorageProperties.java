package com.watermarking.infrastructure.storage;

import org.springframework.boot.context.properties.ConfigurationProperties;

import java.time.Duration;

/**
 * 与 Flask {@code INSTANCE_PATH} + {@code MEDIA_FOLDERS} 根目录语义一致；大小上限对齐
 * {@code watermark/utils/file_config.py} 中环境变量默认值（100MB）。阶段 3：对象存储与 STS。
 */
@ConfigurationProperties(prefix = "wm.storage")
public class WmStorageProperties {

    /**
     * 对应 Flask {@code INSTANCE_PATH}（相对路径则相对 JVM 工作目录解析为绝对路径）。
     */
    private String instancePath = "instance";

    /**
     * {@code minio}：S3 兼容预签名（开发默认）；{@code cos}：腾讯云 CAM STS（需配置 cos.policy-json 等）。
     */
    private String backend = "minio";

    private Limits limits = new Limits();

    /** MinIO / S3 兼容端点与凭据 */
    private Minio minio = new Minio();

    /** 腾讯云 STS（生产）；密钥仅来自环境变量或外部配置 */
    private Cos cos = new Cos();

    /** 直传 PUT 预签名有效期 */
    private Duration presignPutTtl = Duration.ofMinutes(15);

    /** GET 下载预签名（302）有效期 */
    private Duration presignGetTtl = Duration.ofMinutes(15);

    /** complete 时服务端计算 SHA256 的最大对象大小（字节），防止 OOM */
    private long maxHashBytes = 104_857_600L;

    public String getInstancePath() {
        return instancePath;
    }

    public void setInstancePath(String instancePath) {
        this.instancePath = instancePath;
    }

    public Limits getLimits() {
        return limits;
    }

    public void setLimits(Limits limits) {
        this.limits = limits;
    }

    public Minio getMinio() {
        return minio;
    }

    public void setMinio(Minio minio) {
        this.minio = minio;
    }

    public Cos getCos() {
        return cos;
    }

    public void setCos(Cos cos) {
        this.cos = cos;
    }

    public String getBackend() {
        return backend;
    }

    public void setBackend(String backend) {
        this.backend = backend;
    }

    public Duration getPresignPutTtl() {
        return presignPutTtl;
    }

    public void setPresignPutTtl(Duration presignPutTtl) {
        this.presignPutTtl = presignPutTtl;
    }

    public Duration getPresignGetTtl() {
        return presignGetTtl;
    }

    public void setPresignGetTtl(Duration presignGetTtl) {
        this.presignGetTtl = presignGetTtl;
    }

    public long getMaxHashBytes() {
        return maxHashBytes;
    }

    public void setMaxHashBytes(long maxHashBytes) {
        this.maxHashBytes = maxHashBytes;
    }

    public long maxBytesForMediaType(String mediaType) {
        return switch (mediaType) {
            case "image" -> limits.getImage();
            case "video" -> limits.getVideo();
            case "audio" -> limits.getAudio();
            case "text" -> limits.getText();
            default -> limits.getDefaultMax();
        };
    }

    public static final class Limits {
        private long image = 104_857_600L;
        private long video = 104_857_600L;
        private long audio = 104_857_600L;
        private long text = 104_857_600L;
        /** 与 Python {@code DEFAULT_MAX_SIZE} 默认一致 */
        private long defaultMax = 104_857_600L;

        public long getImage() {
            return image;
        }

        public void setImage(long image) {
            this.image = image;
        }

        public long getVideo() {
            return video;
        }

        public void setVideo(long video) {
            this.video = video;
        }

        public long getAudio() {
            return audio;
        }

        public void setAudio(long audio) {
            this.audio = audio;
        }

        public long getText() {
            return text;
        }

        public void setText(long text) {
            this.text = text;
        }

        public long getDefaultMax() {
            return defaultMax;
        }

        public void setDefaultMax(long defaultMax) {
            this.defaultMax = defaultMax;
        }
    }

    public static final class Minio {
        private String endpoint = "";
        private String accessKey = "";
        private String secretKey = "";
        private String bucket = "watermark";
        private String region = "us-east-1";

        public String getEndpoint() {
            return endpoint;
        }

        public void setEndpoint(String endpoint) {
            this.endpoint = endpoint;
        }

        public String getAccessKey() {
            return accessKey;
        }

        public void setAccessKey(String accessKey) {
            this.accessKey = accessKey;
        }

        public String getSecretKey() {
            return secretKey;
        }

        public void setSecretKey(String secretKey) {
            this.secretKey = secretKey;
        }

        public String getBucket() {
            return bucket;
        }

        public void setBucket(String bucket) {
            this.bucket = bucket;
        }

        public String getRegion() {
            return region;
        }

        public void setRegion(String region) {
            this.region = region;
        }
    }

    public static final class Cos {
        private String secretId = "";
        private String secretKey = "";
        private String region = "ap-guangzhou";
        private String bucket = "";
        /**
         * 传给 GetFederationToken 的 CAM 策略 JSON（需包含 cos:PutObject 等）。
         * 可使用占位符 {@code ${allowedPrefix}}，服务端会替换为本次生成的对象键前缀（不含末尾 *）。
         */
        private String policyJson = "";
        private Duration stsDuration = Duration.ofMinutes(15);

        public String getSecretId() {
            return secretId;
        }

        public void setSecretId(String secretId) {
            this.secretId = secretId;
        }

        public String getSecretKey() {
            return secretKey;
        }

        public void setSecretKey(String secretKey) {
            this.secretKey = secretKey;
        }

        public String getRegion() {
            return region;
        }

        public void setRegion(String region) {
            this.region = region;
        }

        public String getBucket() {
            return bucket;
        }

        public void setBucket(String bucket) {
            this.bucket = bucket;
        }

        public String getPolicyJson() {
            return policyJson;
        }

        public void setPolicyJson(String policyJson) {
            this.policyJson = policyJson;
        }

        public Duration getStsDuration() {
            return stsDuration;
        }

        public void setStsDuration(Duration stsDuration) {
            this.stsDuration = stsDuration;
        }
    }
}

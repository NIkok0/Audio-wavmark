package com.watermarking.application.jobs;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.watermarking.domain.model.File;
import com.watermarking.infrastructure.jobs.IdempotencyKeyHasher;
import com.watermarking.infrastructure.jobs.RedisWatermarkJobStateRepository;
import com.watermarking.infrastructure.jobs.RedisWatermarkStreamPublisher;
import com.watermarking.infrastructure.storage.S3ObjectStorageService;
import com.watermarking.infrastructure.storage.S3UriParser;
import com.watermarking.infrastructure.storage.WmStorageProperties;
import io.micrometer.core.instrument.MeterRegistry;
import org.springframework.stereotype.Service;

import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

@Service
public class WatermarkJobService {

    private final WatermarkJobFilePreparer filePreparer;
    private final JobEnqueueRecoveryService recoveryService;
    private final RedisWatermarkJobStateRepository jobState;
    private final RedisWatermarkStreamPublisher streamPublisher;
    private final S3ObjectStorageService s3ObjectStorageService;
    private final WmStorageProperties storageProperties;
    private final ObjectMapper objectMapper;
    private final MeterRegistry meterRegistry;

    public WatermarkJobService(
            WatermarkJobFilePreparer filePreparer,
            JobEnqueueRecoveryService recoveryService,
            RedisWatermarkJobStateRepository jobState,
            RedisWatermarkStreamPublisher streamPublisher,
            S3ObjectStorageService s3ObjectStorageService,
            WmStorageProperties storageProperties,
            ObjectMapper objectMapper,
            MeterRegistry meterRegistry) {
        this.filePreparer = filePreparer;
        this.recoveryService = recoveryService;
        this.jobState = jobState;
        this.streamPublisher = streamPublisher;
        this.s3ObjectStorageService = s3ObjectStorageService;
        this.storageProperties = storageProperties;
        this.objectMapper = objectMapper;
        this.meterRegistry = meterRegistry;
    }

    public WatermarkJobResponse getForUser(int userId, String jobId) {
        Map<String, String> m =
                jobState.getJob(jobId).orElseThrow(() -> new WatermarkJobNotFoundException("任务不存在"));
        int uid = Integer.parseInt(m.getOrDefault("userId", "-1"));
        if (uid != userId) {
            throw new WatermarkJobNotFoundException("任务不存在");
        }
        return toResponse(jobId, m);
    }

    public WatermarkJobResponse enqueue(int userId, CreateWatermarkJobRequest req, String idempotencyKeyRaw) {
        if (idempotencyKeyRaw != null && !idempotencyKeyRaw.isBlank()) {
            String hash = IdempotencyKeyHasher.sha256Hex(idempotencyKeyRaw);
            Optional<String> existing = jobState.getIdempotencyJobId(userId, hash);
            if (existing.isPresent()) {
                return getForUser(userId, existing.get());
            }
        }

        String jobId = UUID.randomUUID().toString();
        File file = filePreparer.markProcessing(userId, req);

        String traceId = UUID.randomUUID().toString();
        StorageSlice slice = resolveStorageSlice(file);
        ObjectNode payload = buildPayload(jobId, file, slice, traceId);

        String json;
        try {
            json = objectMapper.writeValueAsString(payload);
        } catch (JsonProcessingException e) {
            recoveryService.revertFileToPendingAfterEnqueueFailure(file.getId(), userId, "序列化任务消息失败");
            recordEnqueue("serialization_error");
            throw new WatermarkJobEnqueueException("序列化任务消息失败", e);
        }

        try {
            jobState.initQueuedJob(jobId, userId, file.getId(), "embed");
            streamPublisher.publishPayloadJson(json);
            if (idempotencyKeyRaw != null && !idempotencyKeyRaw.isBlank()) {
                jobState.bindIdempotencyKey(userId, IdempotencyKeyHasher.sha256Hex(idempotencyKeyRaw), jobId);
            }
        } catch (RuntimeException e) {
            recoveryService.revertFileToPendingAfterEnqueueFailure(file.getId(), userId, "入队失败");
            recordEnqueue("redis_or_publish_error");
            throw new WatermarkJobEnqueueException("入队失败", e);
        }

        recordEnqueue("accepted");
        return getForUser(userId, jobId);
    }

    private WatermarkJobResponse toResponse(String jobId, Map<String, String> m) {
        long created = Long.parseLong(m.getOrDefault("createdAt", "0"));
        long updated = Long.parseLong(m.getOrDefault("updatedAt", "0"));
        return WatermarkJobResponse.fromRedisFields(
                jobId,
                m.getOrDefault("status", "UNKNOWN"),
                Integer.parseInt(m.getOrDefault("fileId", "0")),
                m.getOrDefault("operation", "embed"),
                m.get("errorMessage"),
                created,
                updated);
    }

    private StorageSlice resolveStorageSlice(File f) {
        String original = f.getOriginalPath();
        Optional<S3UriParser.Parsed> s3 = S3UriParser.tryParse(original);
        if (s3.isPresent()) {
            if (!s3ObjectStorageService.isEnabled()) {
                throw new InvalidWatermarkJobStateException("对象存储未启用，无法处理 s3:// 路径");
            }
            if (!s3.get().bucket().equals(s3ObjectStorageService.getBucket())) {
                throw new InvalidWatermarkJobStateException("对象的 bucket 与当前配置不一致");
            }
            return new StorageSlice(s3.get().bucket(), regionForConfiguredBackend(), s3.get().key());
        }
        return new StorageSlice("", "", original);
    }

    private String regionForConfiguredBackend() {
        String b = storageProperties.getBackend() == null ? "minio" : storageProperties.getBackend().toLowerCase(Locale.ROOT);
        if ("cos".equals(b)) {
            return storageProperties.getCos().getRegion();
        }
        return storageProperties.getMinio().getRegion();
    }

    private ObjectNode buildPayload(String jobId, File file, StorageSlice slice, String traceId) {
        ObjectNode n = objectMapper.createObjectNode();
        n.put("jobId", jobId);
        n.put("fileId", file.getId());
        n.put("operation", "embed");
        n.put("objectKey", slice.objectKey());
        n.put("bucket", slice.bucket());
        n.put("region", slice.region());
        n.put("mediaType", file.getFileType());
        n.put("watermarkText", file.getWatermarkText() != null ? file.getWatermarkText() : "");
        if (file.getWatermarkSeed() != null && !file.getWatermarkSeed().isBlank()) {
            n.put("watermarkSeed", file.getWatermarkSeed());
        } else {
            n.putNull("watermarkSeed");
        }
        if (file.getWatermarkType() != null && !file.getWatermarkType().isBlank()) {
            n.put("algorithm", file.getWatermarkType());
        } else {
            n.putNull("algorithm");
        }
        n.put("traceId", traceId);
        return n;
    }

    private record StorageSlice(String bucket, String region, String objectKey) {}

    private void recordEnqueue(String outcome) {
        meterRegistry.counter("wm.jobs.enqueue", "outcome", outcome).increment();
    }
}

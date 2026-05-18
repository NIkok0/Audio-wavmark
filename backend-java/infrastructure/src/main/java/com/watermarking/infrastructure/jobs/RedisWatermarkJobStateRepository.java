package com.watermarking.infrastructure.jobs;

import com.watermarking.infrastructure.config.WmJobsProperties;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Repository;

import java.time.Duration;
import java.time.Instant;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

@Repository
public class RedisWatermarkJobStateRepository {

    private final StringRedisTemplate redis;
    private final WmJobsProperties jobsProperties;

    public RedisWatermarkJobStateRepository(StringRedisTemplate redis, WmJobsProperties jobsProperties) {
        this.redis = redis;
        this.jobsProperties = jobsProperties;
    }

    public void initQueuedJob(String jobId, int userId, int fileId, String operation) {
        long now = Instant.now().toEpochMilli();
        Map<String, String> map = new HashMap<>();
        map.put("status", "QUEUED");
        map.put("userId", Integer.toString(userId));
        map.put("fileId", Integer.toString(fileId));
        map.put("operation", operation);
        map.put("createdAt", Long.toString(now));
        map.put("updatedAt", Long.toString(now));
        map.put("errorMessage", "");
        redis.opsForHash().putAll(jobsProperties.jobHashKey(jobId), map);
    }

    public Optional<Map<String, String>> getJob(String jobId) {
        Map<Object, Object> raw = redis.opsForHash().entries(jobsProperties.jobHashKey(jobId));
        if (raw == null || raw.isEmpty()) {
            return Optional.empty();
        }
        Map<String, String> out = new HashMap<>();
        raw.forEach((k, v) -> out.put(String.valueOf(k), v == null ? "" : String.valueOf(v)));
        return Optional.of(Collections.unmodifiableMap(out));
    }

    public Optional<String> getIdempotencyJobId(int userId, String idempotencyKeyHash) {
        String v = redis.opsForValue().get(jobsProperties.idempotencyRedisKey(userId, idempotencyKeyHash));
        return Optional.ofNullable(v).filter(s -> !s.isBlank());
    }

    public void bindIdempotencyKey(int userId, String idempotencyKeyHash, String jobId) {
        redis.opsForValue()
                .set(
                        jobsProperties.idempotencyRedisKey(userId, idempotencyKeyHash),
                        jobId,
                        jobsProperties.getIdempotencyTtl() != null
                                ? jobsProperties.getIdempotencyTtl()
                                : Duration.ofHours(24));
    }
}

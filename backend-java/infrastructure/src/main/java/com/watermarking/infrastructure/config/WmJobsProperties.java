package com.watermarking.infrastructure.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

import java.time.Duration;

/**
 * 阶段 4：Redis Streams 入队与任务态 Hash；Key 前缀与 docs/watermark-java-backend-tech-selection.md §10.2 一致。
 */
@ConfigurationProperties(prefix = "wm.jobs")
public class WmJobsProperties {

    /** Redis Stream 名称 */
    private String streamKey = "wm:stream:watermark";

    /** Worker 消费组（Python 侧 {@code XGROUP CREATE} 使用同一名称） */
    private String consumerGroup = "wm:workers";

    /** 任务态 Hash：{@code wm:job:{jobId}} */
    private String jobKeyPrefix = "wm:job:";

    /** 幂等：{@code wm:idem:{userId}:{hash}} */
    private String idempotencyKeyPrefix = "wm:idem:";

    /** Idempotency-Key 映射 TTL */
    private Duration idempotencyTtl = Duration.ofHours(24);

    public String getStreamKey() {
        return streamKey;
    }

    public void setStreamKey(String streamKey) {
        this.streamKey = streamKey;
    }

    public String getConsumerGroup() {
        return consumerGroup;
    }

    public void setConsumerGroup(String consumerGroup) {
        this.consumerGroup = consumerGroup;
    }

    public String getJobKeyPrefix() {
        return jobKeyPrefix;
    }

    public void setJobKeyPrefix(String jobKeyPrefix) {
        this.jobKeyPrefix = jobKeyPrefix;
    }

    public String getIdempotencyKeyPrefix() {
        return idempotencyKeyPrefix;
    }

    public void setIdempotencyKeyPrefix(String idempotencyKeyPrefix) {
        this.idempotencyKeyPrefix = idempotencyKeyPrefix;
    }

    public Duration getIdempotencyTtl() {
        return idempotencyTtl;
    }

    public void setIdempotencyTtl(Duration idempotencyTtl) {
        this.idempotencyTtl = idempotencyTtl;
    }

    public String jobHashKey(String jobId) {
        return jobKeyPrefix + jobId;
    }

    public String idempotencyRedisKey(int userId, String idempotencyKeyHash) {
        return idempotencyKeyPrefix + userId + ":" + idempotencyKeyHash;
    }
}

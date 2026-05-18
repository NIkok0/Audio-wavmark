package com.watermarking.infrastructure.jobs;

import com.watermarking.infrastructure.config.WmJobsProperties;
import io.github.resilience4j.retry.annotation.Retry;
import org.springframework.data.redis.connection.stream.StreamRecords;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

import java.util.Map;

/**
 * 将任务 JSON 写入 Redis Stream；{@link Retry} 由 Resilience4j 保护（配置名 {@code redisStreamPublish}）。
 */
@Component
public class RedisWatermarkStreamPublisher {

    private final StringRedisTemplate redis;
    private final WmJobsProperties jobsProperties;

    public RedisWatermarkStreamPublisher(StringRedisTemplate redis, WmJobsProperties jobsProperties) {
        this.redis = redis;
        this.jobsProperties = jobsProperties;
    }

    @Retry(name = "redisStreamPublish")
    public void publishPayloadJson(String payloadJson) {
        var record = StreamRecords.string(Map.of("payload", payloadJson)).withStreamKey(jobsProperties.getStreamKey());
        redis.opsForStream().add(record);
    }
}

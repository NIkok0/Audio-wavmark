package com.watermarking.web.metrics;

import com.watermarking.infrastructure.config.WmJobsProperties;
import io.micrometer.core.instrument.Gauge;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.binder.MeterBinder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.core.StringRedisTemplate;

/**
 * 队列深度（Redis Stream {@code XLEN} 近似）；与《选型》第 13 节「队列深度」对齐。
 */
@Configuration
public class WmQueueMetricsConfiguration {

    @Bean
    public MeterBinder watermarkJobStreamLengthGauge(StringRedisTemplate redis, WmJobsProperties jobsProperties) {
        return registry ->
                Gauge.builder(
                                "wm.jobs.redis_stream.length",
                                redis,
                                r -> {
                                    try {
                                        Long len = r.opsForStream().size(jobsProperties.getStreamKey());
                                        return len == null ? 0.0 : len.doubleValue();
                                    } catch (RuntimeException ignored) {
                                        return 0.0;
                                    }
                                })
                        .description("Redis Stream 长度（近似队列深度）")
                        .register(registry);
    }
}

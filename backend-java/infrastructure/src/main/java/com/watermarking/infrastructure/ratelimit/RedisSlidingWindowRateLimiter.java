package com.watermarking.infrastructure.ratelimit;

import com.watermarking.infrastructure.config.WmRateLimitProperties;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.util.UUID;

@Component
public class RedisSlidingWindowRateLimiter {

    private final StringRedisTemplate redis;
    private final WmRateLimitProperties props;

    public RedisSlidingWindowRateLimiter(StringRedisTemplate redis, WmRateLimitProperties props) {
        this.redis = redis;
        this.props = props;
    }

    /**
     * @param redisKeySuffix 已包含 userId 或 IP 等区分维度
     * @return false 表示超过配额
     */
    public boolean allow(String redisKeySuffix, int maxPerWindow) {
        if (!props.isEnabled()) {
            return true;
        }
        int win = Math.max(1, props.getWindowSeconds());
        long now = System.currentTimeMillis();
        long minScore = now - win * 1000L;
        String key = "wm:rl:" + redisKeySuffix;

        redis.opsForZSet().removeRangeByScore(key, 0, minScore);
        Long n = redis.opsForZSet().zCard(key);
        if (n != null && n >= maxPerWindow) {
            return false;
        }
        redis.opsForZSet().add(key, UUID.randomUUID().toString(), now);
        redis.expire(key, Duration.ofSeconds(win + 5));
        return true;
    }
}

package com.watermarking.infrastructure.lock;

import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

import java.time.Duration;

@Component
public class RedisDistributedLock {

    private final StringRedisTemplate redis;

    public RedisDistributedLock(StringRedisTemplate redis) {
        this.redis = redis;
    }

    /**
     * @return true 表示成功获取锁
     */
    public boolean tryLock(String key, Duration ttl) {
        if (key == null || key.isBlank()) {
            return false;
        }
        Duration d = ttl != null && !ttl.isNegative() && !ttl.isZero() ? ttl : Duration.ofMinutes(5);
        Boolean ok = redis.opsForValue().setIfAbsent(key, "1", d);
        return Boolean.TRUE.equals(ok);
    }

    public void unlock(String key) {
        if (key != null && !key.isBlank()) {
            redis.delete(key);
        }
    }
}

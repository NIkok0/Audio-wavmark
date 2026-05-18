package com.watermarking.application.retention;

import com.watermarking.infrastructure.config.WmRetentionProperties;
import com.watermarking.infrastructure.lock.RedisDistributedLock;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
public class RetentionCleanupRunner {

    private static final Logger log = LoggerFactory.getLogger(RetentionCleanupRunner.class);

    private final WmRetentionProperties props;
    private final RedisDistributedLock lock;
    private final RetentionCleanupService cleanupService;

    public RetentionCleanupRunner(
            WmRetentionProperties props, RedisDistributedLock lock, RetentionCleanupService cleanupService) {
        this.props = props;
        this.lock = lock;
        this.cleanupService = cleanupService;
    }

    @Scheduled(cron = "${wm.retention.cleanup-cron:0 0 2 * * *}")
    public void scheduledCleanup() {
        if (!props.isCleanupEnabled()) {
            return;
        }
        if (!lock.tryLock(props.getLockKey(), props.getLockTtl())) {
            log.debug("retention cleanup skipped: lock not acquired");
            return;
        }
        try {
            cleanupService.runOnce();
        } catch (RuntimeException e) {
            log.error("retention cleanup failed", e);
        } finally {
            lock.unlock(props.getLockKey());
        }
    }
}

package com.watermarking.infrastructure.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

import java.time.Duration;

/**
 * 用户文件保留期清理：与 Flask {@code _user_cleanup_worker} 语义对齐（按 {@code files.created_at}）。
 * 对象生命周期规则由云侧配置；此处仅删库内元数据与本服务可达的 MinIO/COS 对象键。
 */
@ConfigurationProperties(prefix = "wm.retention")
public class WmRetentionProperties {

    /** 是否启用定时清理 */
    private boolean cleanupEnabled = true;

    /** Spring cron，默认每天 02:00 UTC */
    private String cleanupCron = "0 0 2 * * *";

    /** 用户未设置 {@code retention_days} 或值无效时的默认保留天数 */
    private int defaultRetentionDays = 7;

    /** 分布式锁 Key（与《选型》wm: 前缀一致） */
    private String lockKey = "wm:lock:retention:cleanup";

    /** 锁持有时间，防止实例崩溃导致长期占锁 */
    private Duration lockTtl = Duration.ofMinutes(15);

    public boolean isCleanupEnabled() {
        return cleanupEnabled;
    }

    public void setCleanupEnabled(boolean cleanupEnabled) {
        this.cleanupEnabled = cleanupEnabled;
    }

    public String getCleanupCron() {
        return cleanupCron;
    }

    public void setCleanupCron(String cleanupCron) {
        this.cleanupCron = cleanupCron;
    }

    public int getDefaultRetentionDays() {
        return defaultRetentionDays;
    }

    public void setDefaultRetentionDays(int defaultRetentionDays) {
        this.defaultRetentionDays = defaultRetentionDays;
    }

    public String getLockKey() {
        return lockKey;
    }

    public void setLockKey(String lockKey) {
        this.lockKey = lockKey;
    }

    public Duration getLockTtl() {
        return lockTtl;
    }

    public void setLockTtl(Duration lockTtl) {
        this.lockTtl = lockTtl;
    }
}

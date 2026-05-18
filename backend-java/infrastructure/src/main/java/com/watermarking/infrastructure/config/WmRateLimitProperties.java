package com.watermarking.infrastructure.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

import java.util.ArrayList;
import java.util.List;

/**
 * 滑动窗口限流（Redis ZSET），对齐《重构》阶段 5「Bucket4j + Redis 或网关」中的 Redis 方案。
 */
@ConfigurationProperties(prefix = "wm.rate-limit")
public class WmRateLimitProperties {

    private boolean enabled = true;

    /** 滑动窗口长度（秒） */
    private int windowSeconds = 60;

    private List<Rule> rules = new ArrayList<>();

    public WmRateLimitProperties() {
        rules.add(new Rule("POST:/api/v1/jobs/watermark", 30));
        rules.add(new Rule("POST:/api/v1/files", 40));
        rules.add(new Rule("POST:/api/v1/files/complete", 60));
        rules.add(new Rule("POST:/api/v1/storage/sts", 120));
        rules.add(new Rule("GET:/api/v1/files/*/content", 120));
    }

    public boolean isEnabled() {
        return enabled;
    }

    public void setEnabled(boolean enabled) {
        this.enabled = enabled;
    }

    public int getWindowSeconds() {
        return windowSeconds;
    }

    public void setWindowSeconds(int windowSeconds) {
        this.windowSeconds = windowSeconds;
    }

    public List<Rule> getRules() {
        return rules;
    }

    public void setRules(List<Rule> rules) {
        this.rules = rules != null ? rules : new ArrayList<>();
    }

    public static final class Rule {
        /**
         * 精确匹配例如 POST:/api/v1/files；若 key 含星号则按 Ant 风格匹配 METHOD:requestURI
         *（例如 GET:/api/v1/files/星号/content，星号表示单段通配）。
         */
        private String key;
        private int maxRequests = 60;

        public Rule() {}

        public Rule(String key, int maxRequests) {
            this.key = key;
            this.maxRequests = maxRequests;
        }

        public String getKey() {
            return key;
        }

        public void setKey(String key) {
            this.key = key;
        }

        public int getMaxRequests() {
            return maxRequests;
        }

        public void setMaxRequests(int maxRequests) {
            this.maxRequests = maxRequests;
        }
    }
}

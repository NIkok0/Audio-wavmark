package com.watermarking.web.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.Arrays;
import java.util.List;

/**
 * 由 {@code wm.cors.*} 属性驱动的 CORS 配置。
 *
 * <p>跨子域部署（例如前端 https://www.loadsadar.asia，API https://api.loadsadar.asia）需要：
 * <ul>
 *   <li>{@code wm.cors.enabled=true}</li>
 *   <li>{@code wm.cors.allowed-origins=https://loadsadar.asia,https://www.loadsadar.asia}</li>
 *   <li>{@code server.servlet.session.cookie.same-site=none}（见 application-prod.yml）</li>
 * </ul>
 *
 * <p>Bean 始终注册；未启用时返回空白名单 Source，等价于不放行任何跨域请求，此时
 * {@link SecurityConfig} 的 {@code .cors(...)} 相当于 no-op。
 */
@Configuration
public class CorsConfig {

    private final boolean enabled;
    private final List<String> allowedOrigins;
    private final List<String> allowedMethods;
    private final List<String> allowedHeaders;
    private final List<String> exposedHeaders;
    private final long maxAgeSeconds;

    public CorsConfig(
            @Value("${wm.cors.enabled:false}") boolean enabled,
            @Value("${wm.cors.allowed-origins:}") String allowedOrigins,
            @Value("${wm.cors.allowed-methods:GET,POST,PUT,PATCH,DELETE,OPTIONS,HEAD}") String allowedMethods,
            @Value("${wm.cors.allowed-headers:*}") String allowedHeaders,
            @Value("${wm.cors.exposed-headers:X-Request-Id}") String exposedHeaders,
            @Value("${wm.cors.max-age-seconds:3600}") long maxAgeSeconds) {
        this.enabled = enabled;
        this.allowedOrigins = splitCsv(allowedOrigins);
        this.allowedMethods = splitCsv(allowedMethods);
        this.allowedHeaders = splitCsv(allowedHeaders);
        this.exposedHeaders = splitCsv(exposedHeaders);
        this.maxAgeSeconds = maxAgeSeconds;
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        if (!enabled || allowedOrigins.isEmpty()) {
            return source;
        }
        CorsConfiguration config = new CorsConfiguration();
        config.setAllowedOrigins(allowedOrigins);
        config.setAllowedMethods(allowedMethods);
        if (allowedHeaders.size() == 1 && "*".equals(allowedHeaders.get(0))) {
            config.addAllowedHeader("*");
        } else {
            config.setAllowedHeaders(allowedHeaders);
        }
        config.setExposedHeaders(exposedHeaders);
        config.setAllowCredentials(true);
        config.setMaxAge(maxAgeSeconds);
        source.registerCorsConfiguration("/api/**", config);
        return source;
    }

    private static List<String> splitCsv(String raw) {
        if (raw == null || raw.isBlank()) {
            return List.of();
        }
        return Arrays.stream(raw.split(","))
                .map(String::trim)
                .filter(s -> !s.isEmpty())
                .toList();
    }
}

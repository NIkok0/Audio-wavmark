package com.watermarking.web.ratelimit;

import com.watermarking.application.auth.DomainUserDetails;
import com.watermarking.infrastructure.config.WmRateLimitProperties;
import com.watermarking.infrastructure.ratelimit.RedisSlidingWindowRateLimiter;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.HttpStatus;
import org.springframework.lang.NonNull;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.util.AntPathMatcher;
import org.springframework.web.servlet.HandlerInterceptor;

import java.io.IOException;
import java.nio.charset.StandardCharsets;

@Component
public class RateLimitInterceptor implements HandlerInterceptor {

    private static final AntPathMatcher PATH = new AntPathMatcher();

    private final WmRateLimitProperties props;
    private final RedisSlidingWindowRateLimiter limiter;

    public RateLimitInterceptor(WmRateLimitProperties props, RedisSlidingWindowRateLimiter limiter) {
        this.props = props;
        this.limiter = limiter;
    }

    @Override
    public boolean preHandle(
            @NonNull HttpServletRequest request, @NonNull HttpServletResponse response, @NonNull Object handler)
            throws IOException {
        if (!props.isEnabled()) {
            return true;
        }
        String method = request.getMethod();
        String uri = request.getRequestURI();
        String combo = method + ":" + uri;

        WmRateLimitProperties.Rule matched = null;
        for (WmRateLimitProperties.Rule r : props.getRules()) {
            if (r.getKey() == null || r.getKey().isBlank()) {
                continue;
            }
            String k = r.getKey();
            if (k.contains("*")) {
                if (PATH.match(k, combo)) {
                    matched = r;
                    break;
                }
            } else if (k.equalsIgnoreCase(combo)) {
                matched = r;
                break;
            }
        }
        if (matched == null) {
            return true;
        }

        String subject = resolveSubject();
        String redisSuffix = matched.getKey() + ":" + subject;
        if (!limiter.allow(redisSuffix, matched.getMaxRequests())) {
            response.setStatus(HttpStatus.TOO_MANY_REQUESTS.value());
            response.setCharacterEncoding(StandardCharsets.UTF_8.name());
            response.setContentType("application/json");
            response.getWriter().write("{\"title\":\"Too Many Requests\",\"status\":429}");
            return false;
        }
        return true;
    }

    private static String resolveSubject() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth != null && auth.getPrincipal() instanceof DomainUserDetails d) {
            return "u:" + d.getUser().getId();
        }
        return "anon";
    }
}

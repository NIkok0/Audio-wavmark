package com.watermarking.application.bootstrap;

import com.watermarking.domain.model.User;
import com.watermarking.infrastructure.persistence.UserRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

/**
 * 空库首次启动时创建 super_admin 账户，便于在完全新部署的环境里登录管理后台。
 *
 * <p>触发条件（全部满足）：
 * <ul>
 *   <li>{@code wm.bootstrap.admin.enabled=true}（默认 false，避免意外在已有库里插数据）</li>
 *   <li>{@code users} 表为空</li>
 *   <li>提供了非空的 {@code wm.bootstrap.admin.username/email/password}</li>
 * </ul>
 *
 * 一旦创建完成，**建议立即把 {@code wm.bootstrap.admin.enabled} 关掉并清理密码环境变量**。
 */
@Component
public class AdminBootstrapRunner implements CommandLineRunner {

    private static final Logger log = LoggerFactory.getLogger(AdminBootstrapRunner.class);

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final boolean enabled;
    private final String username;
    private final String email;
    private final String password;

    public AdminBootstrapRunner(
            UserRepository userRepository,
            PasswordEncoder passwordEncoder,
            @Value("${wm.bootstrap.admin.enabled:false}") boolean enabled,
            @Value("${wm.bootstrap.admin.username:}") String username,
            @Value("${wm.bootstrap.admin.email:}") String email,
            @Value("${wm.bootstrap.admin.password:}") String password) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.enabled = enabled;
        this.username = username;
        this.email = email;
        this.password = password;
    }

    @Override
    @Transactional
    public void run(String... args) {
        if (!enabled) {
            return;
        }
        if (isBlank(username) || isBlank(email) || isBlank(password)) {
            log.warn("Admin bootstrap enabled but username/email/password missing; skipping.");
            return;
        }
        long existing = userRepository.count();
        if (existing > 0) {
            log.info("Admin bootstrap skipped: users table is not empty (count={}).", existing);
            return;
        }
        User admin = new User();
        admin.setUsername(username.trim());
        admin.setEmail(email.trim());
        admin.setPassword(passwordEncoder.encode(password));
        admin.setAdmin(true);
        admin.setRole("super_admin");
        admin.setActive(true);
        admin.setEmbed(true);
        admin.setExtract(true);
        userRepository.save(admin);
        log.warn("Admin bootstrap created super_admin user '{}'. Disable wm.bootstrap.admin.enabled and rotate the password now.", admin.getUsername());
    }

    private static boolean isBlank(String s) {
        return s == null || s.trim().isEmpty();
    }
}

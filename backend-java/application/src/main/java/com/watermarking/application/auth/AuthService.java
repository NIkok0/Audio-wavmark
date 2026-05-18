package com.watermarking.application.auth;

import com.watermarking.domain.model.User;
import com.watermarking.infrastructure.persistence.UserRepository;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AuthService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public AuthService(UserRepository userRepository, PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Transactional
    public User register(String username, String email, String rawPassword) {
        if (userRepository.findByUsername(username).isPresent()) {
            throw new RegistrationConflictException(
                    RegistrationConflictException.ConflictField.USERNAME, "该用户名已存在！");
        }
        if (userRepository.findByEmail(email).isPresent()) {
            throw new RegistrationConflictException(
                    RegistrationConflictException.ConflictField.EMAIL, "该邮箱已注册！");
        }
        User user = new User();
        user.setUsername(username);
        user.setEmail(email);
        user.setPassword(passwordEncoder.encode(rawPassword));
        return userRepository.save(user);
    }

    /**
     * 登录成功后：若库中仍为 Werkzeug 格式，则静默替换为 BCrypt（与 Flask 静默升级一致）。
     */
    @Transactional
    public void upgradeLegacyPasswordHashIfPresent(Integer userId, String rawPassword) {
        User user = userRepository.findById(userId).orElse(null);
        if (user == null) {
            return;
        }
        String stored = user.getPassword();
        if (stored != null && WerkzeugPasswordHasher.isWerkzeugFormat(stored)) {
            user.setPassword(passwordEncoder.encode(rawPassword));
            userRepository.save(user);
        }
    }
}

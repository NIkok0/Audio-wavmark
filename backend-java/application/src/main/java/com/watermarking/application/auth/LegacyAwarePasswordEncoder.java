package com.watermarking.application.auth;

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;

/**
 * 新密码一律 BCrypt；校验时兼容 Werkzeug {@code pbkdf2:…} / {@code scrypt:…}（与 Flask 遗留库一致）。
 */
public final class LegacyAwarePasswordEncoder implements PasswordEncoder {

    private final BCryptPasswordEncoder bcrypt = new BCryptPasswordEncoder();

    @Override
    public String encode(CharSequence rawPassword) {
        return bcrypt.encode(rawPassword);
    }

    @Override
    public boolean matches(CharSequence rawPassword, String encodedPassword) {
        if (encodedPassword == null || rawPassword == null) {
            return false;
        }
        if (looksLikeBcrypt(encodedPassword)) {
            return bcrypt.matches(rawPassword, encodedPassword);
        }
        if (WerkzeugPasswordHasher.isWerkzeugFormat(encodedPassword)) {
            return WerkzeugPasswordHasher.matches(encodedPassword, rawPassword.toString());
        }
        return false;
    }

    private static boolean looksLikeBcrypt(String encodedPassword) {
        return encodedPassword.startsWith("$2a$")
                || encodedPassword.startsWith("$2b$")
                || encodedPassword.startsWith("$2y$");
    }
}

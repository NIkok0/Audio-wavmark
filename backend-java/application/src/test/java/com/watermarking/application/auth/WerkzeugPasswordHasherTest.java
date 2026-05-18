package com.watermarking.application.auth;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class WerkzeugPasswordHasherTest {

    @Test
    void matchesPbkdf2Sha256_lowIterations() throws Exception {
        String stored =
                WerkzeugPasswordHasher.formatPbkdf2HashForTest("sha256", 50, "test-salt-1", "mySecretPassword");
        assertThat(WerkzeugPasswordHasher.matches(stored, "mySecretPassword")).isTrue();
        assertThat(WerkzeugPasswordHasher.matches(stored, "wrong")).isFalse();
        assertThat(WerkzeugPasswordHasher.isWerkzeugFormat(stored)).isTrue();
    }

    @Test
    void matchesScrypt_smallN() throws Exception {
        String stored = WerkzeugPasswordHasher.formatScryptHashForTest(4096, 8, 1, "scrypt-salt-x", "passw0rd!");
        assertThat(WerkzeugPasswordHasher.matches(stored, "passw0rd!")).isTrue();
        assertThat(WerkzeugPasswordHasher.matches(stored, "nope")).isFalse();
    }

    @Test
    void rejectsMalformed() {
        assertThat(WerkzeugPasswordHasher.matches("pbkdf2:sha256:10$onlyonepart", "x")).isFalse();
        assertThat(WerkzeugPasswordHasher.matches("$2a$10$N9qo8uLOickgx2ZMRZoMye", "x")).isFalse();
    }
}

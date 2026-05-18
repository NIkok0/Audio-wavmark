package com.watermarking.application.auth;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class LegacyAwarePasswordEncoderTest {

    private final LegacyAwarePasswordEncoder encoder = new LegacyAwarePasswordEncoder();

    @Test
    void bcryptRoundTrip() {
        String enc = encoder.encode("hello-bcrypt");
        assertThat(encoder.matches("hello-bcrypt", enc)).isTrue();
        assertThat(encoder.matches("other", enc)).isFalse();
    }

    @Test
    void werkzeugPbkdf2ThroughEncoder() throws Exception {
        String stored = WerkzeugPasswordHasher.formatPbkdf2HashForTest("sha256", 80, "s2", "p@ss");
        assertThat(encoder.matches("p@ss", stored)).isTrue();
        assertThat(encoder.matches("p@ss2", stored)).isFalse();
    }
}

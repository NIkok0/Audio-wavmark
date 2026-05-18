package com.watermarking.infrastructure.jobs;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class IdempotencyKeyHasherTest {

    @Test
    void sha256HexIsStableForSameInput() {
        String a = IdempotencyKeyHasher.sha256Hex("my-idempotency-key");
        String b = IdempotencyKeyHasher.sha256Hex("my-idempotency-key");
        assertThat(a).isEqualTo(b).hasSize(64);
    }

    @Test
    void blankReturnsEmpty() {
        assertThat(IdempotencyKeyHasher.sha256Hex(null)).isEmpty();
        assertThat(IdempotencyKeyHasher.sha256Hex("")).isEmpty();
        assertThat(IdempotencyKeyHasher.sha256Hex("   ")).isEmpty();
    }
}

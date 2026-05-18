package com.watermarking.application.auth;

import com.watermarking.domain.model.User;
import org.junit.jupiter.api.Test;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.time.Instant;

import static org.junit.jupiter.api.Assertions.assertEquals;

class DomainUserDetailsSerializationTest {

    @Test
    void roundTripThroughJavaSerialization() throws Exception {
        User source = new User();
        source.setId(1);
        source.setUsername("admin");
        source.setEmail("admin@example.com");
        source.setPassword("$2b$10$hash");
        source.setAdmin(true);
        source.setRole("super_admin");
        source.setActive(true);
        source.setCreatedAt(Instant.parse("2026-01-01T00:00:00Z"));
        source.setUpdatedAt(Instant.parse("2026-01-01T00:00:00Z"));

        DomainUserDetails details = new DomainUserDetails(source);

        byte[] bytes;
        try (ByteArrayOutputStream bos = new ByteArrayOutputStream();
                ObjectOutputStream oos = new ObjectOutputStream(bos)) {
            oos.writeObject(details);
            bytes = bos.toByteArray();
        }

        try (ObjectInputStream ois = new ObjectInputStream(new ByteArrayInputStream(bytes))) {
            DomainUserDetails restored = (DomainUserDetails) ois.readObject();
            assertEquals("admin", restored.getUsername());
            assertEquals(1, restored.getUser().getId());
        }
    }
}

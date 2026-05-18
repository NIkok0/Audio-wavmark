package com.watermarking.infrastructure.storage;

import java.io.IOException;
import java.io.InputStream;
import java.security.DigestInputStream;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;

public final class Sha256Util {

    private Sha256Util() {}

    public static String sha256Hex(InputStream in, long maxBytes) throws IOException {
        MessageDigest digest;
        try {
            digest = MessageDigest.getInstance("SHA-256");
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException(e);
        }
        try (DigestInputStream dis = new DigestInputStream(in, digest)) {
            byte[] buf = new byte[65536];
            long total = 0;
            int n;
            while ((n = dis.read(buf)) >= 0) {
                total += n;
                if (total > maxBytes) {
                    throw new IllegalArgumentException("对象过大，超过服务端哈希上限");
                }
            }
            return HexFormat.of().formatHex(digest.digest());
        }
    }
}

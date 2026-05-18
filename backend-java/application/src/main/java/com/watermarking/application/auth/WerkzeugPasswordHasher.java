package com.watermarking.application.auth;

import org.bouncycastle.crypto.generators.SCrypt;

import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.spec.InvalidKeySpecException;
import java.util.HexFormat;

/**
 * 兼容 Flask / Werkzeug {@code generate_password_hash} 存储格式（与 {@code check_password_hash} 对齐）。
 * <p>
 * 支持：<code>pbkdf2:sha256:…$salt$hexdigest</code>、<code>scrypt:n:r:p$salt$hexdigest</code>。
 * Salt 与 Werkzeug 一致为 <strong>字符串的 UTF-8 字节</strong>（非 Base64 解码）。
 */
public final class WerkzeugPasswordHasher {

    private static final int PBKDF2_DEFAULT_ITERATIONS = 1_000_000;
    private static final int SCRYPT_DEFAULT_N = 32_768;
    private static final int SCRYPT_DEFAULT_R = 8;
    private static final int SCRYPT_DEFAULT_P = 1;
    private static final int SCRYPT_DK_LEN = 64;

    private WerkzeugPasswordHasher() {}

    public static boolean isWerkzeugFormat(String storedHash) {
        if (storedHash == null || storedHash.isEmpty()) {
            return false;
        }
        return storedHash.startsWith("pbkdf2:") || storedHash.startsWith("scrypt:");
    }

    /**
     * @return 与 Werkzeug {@code check_password_hash} 一致
     */
    public static boolean matches(String storedHash, String rawPassword) {
        if (storedHash == null || rawPassword == null) {
            return false;
        }
        if (!isWerkzeugFormat(storedHash)) {
            return false;
        }
        final String method;
        final String salt;
        final String expectedHex;
        try {
            int first = storedHash.indexOf('$');
            int second = storedHash.indexOf('$', first + 1);
            if (first < 0 || second < 0 || second >= storedHash.length() - 1) {
                return false;
            }
            method = storedHash.substring(0, first);
            salt = storedHash.substring(first + 1, second);
            expectedHex = storedHash.substring(second + 1);
        } catch (RuntimeException e) {
            return false;
        }
        try {
            String computedHex;
            if (method.startsWith("pbkdf2")) {
                computedHex = pbkdf2Hex(method, salt, rawPassword);
            } else if (method.startsWith("scrypt")) {
                computedHex = scryptHex(method, salt, rawPassword);
            } else {
                return false;
            }
            byte[] expected = HexFormat.of().parseHex(expectedHex.trim());
            byte[] computed = HexFormat.of().parseHex(computedHex);
            return MessageDigest.isEqual(expected, computed);
        } catch (Exception e) {
            return false;
        }
    }

    static String formatPbkdf2HashForTest(String hashName, int iterations, String salt, String rawPassword)
            throws Exception {
        String methodField = "pbkdf2:" + hashName + ":" + iterations;
        return methodField + "$" + salt + "$" + pbkdf2Hex(methodField, salt, rawPassword);
    }

    static String formatScryptHashForTest(int n, int r, int p, String salt, String rawPassword) throws Exception {
        String methodField = "scrypt:" + n + ":" + r + ":" + p;
        return methodField + "$" + salt + "$" + scryptHex(methodField, salt, rawPassword);
    }

    static String pbkdf2Hex(String methodField, String salt, String rawPassword)
            throws NoSuchAlgorithmException, InvalidKeySpecException {
        String[] mp = methodField.split(":");
        if (mp.length < 1 || !"pbkdf2".equals(mp[0])) {
            throw new IllegalArgumentException("not pbkdf2");
        }
        String hashName = mp.length >= 2 ? mp[1] : "sha256";
        int iterations = mp.length >= 3 ? Integer.parseInt(mp[2]) : PBKDF2_DEFAULT_ITERATIONS;
        String jcaAlg = pbkdf2JcaAlgorithm(hashName);
        byte[] saltBytes = salt.getBytes(StandardCharsets.UTF_8);
        int keyLenBytes = digestLengthBytes(hashName);
        PBEKeySpec spec = new PBEKeySpec(rawPassword.toCharArray(), saltBytes, iterations, keyLenBytes * 8);
        SecretKeyFactory skf = SecretKeyFactory.getInstance(jcaAlg);
        byte[] dk = skf.generateSecret(spec).getEncoded();
        return HexFormat.of().formatHex(dk);
    }

    private static String pbkdf2JcaAlgorithm(String hashName) {
        return switch (hashName.toLowerCase()) {
            case "sha256" -> "PBKDF2WithHmacSHA256";
            case "sha512" -> "PBKDF2WithHmacSHA512";
            case "sha1" -> "PBKDF2WithHmacSHA1";
            default -> throw new IllegalArgumentException("Unsupported pbkdf2 hash: " + hashName);
        };
    }

    private static int digestLengthBytes(String hashName) throws NoSuchAlgorithmException {
        return switch (hashName.toLowerCase()) {
            case "sha256" -> 32;
            case "sha512" -> 64;
            case "sha1" -> 20;
            default -> MessageDigest.getInstance(hashName.toUpperCase()).getDigestLength();
        };
    }

    static String scryptHex(String methodField, String salt, String rawPassword) {
        String[] mp = methodField.split(":");
        if (mp.length < 1 || !"scrypt".equals(mp[0])) {
            throw new IllegalArgumentException("not scrypt");
        }
        int n = mp.length >= 2 ? Integer.parseInt(mp[1]) : SCRYPT_DEFAULT_N;
        int r = mp.length >= 3 ? Integer.parseInt(mp[2]) : SCRYPT_DEFAULT_R;
        int p = mp.length >= 4 ? Integer.parseInt(mp[3]) : SCRYPT_DEFAULT_P;
        byte[] passwordBytes = rawPassword.getBytes(StandardCharsets.UTF_8);
        byte[] saltBytes = salt.getBytes(StandardCharsets.UTF_8);
        byte[] dk = SCrypt.generate(passwordBytes, saltBytes, n, r, p, SCRYPT_DK_LEN);
        return HexFormat.of().formatHex(dk);
    }
}

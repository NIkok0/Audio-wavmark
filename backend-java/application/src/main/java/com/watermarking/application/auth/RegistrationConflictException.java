package com.watermarking.application.auth;

public class RegistrationConflictException extends RuntimeException {

    private final ConflictField field;

    public RegistrationConflictException(ConflictField field, String message) {
        super(message);
        this.field = field;
    }

    public ConflictField getField() {
        return field;
    }

    public enum ConflictField {
        USERNAME,
        EMAIL
    }
}

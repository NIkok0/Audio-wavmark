package com.watermarking.infrastructure.storage;

public class ObjectStorageUnavailableException extends RuntimeException {

    public ObjectStorageUnavailableException(String message) {
        super(message);
    }

    public ObjectStorageUnavailableException(String message, Throwable cause) {
        super(message, cause);
    }
}

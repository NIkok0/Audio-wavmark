package com.watermarking.application.files;

public class InvalidFileUploadException extends RuntimeException {

    public InvalidFileUploadException(String message) {
        super(message);
    }
}

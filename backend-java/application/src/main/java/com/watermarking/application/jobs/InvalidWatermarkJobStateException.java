package com.watermarking.application.jobs;

public class InvalidWatermarkJobStateException extends RuntimeException {

    public InvalidWatermarkJobStateException(String message) {
        super(message);
    }
}

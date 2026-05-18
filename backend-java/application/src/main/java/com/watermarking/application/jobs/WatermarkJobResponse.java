package com.watermarking.application.jobs;

import java.time.Instant;

public record WatermarkJobResponse(
        String jobId,
        String status,
        int fileId,
        String operation,
        String errorMessage,
        Instant createdAt,
        Instant updatedAt) {

    public static WatermarkJobResponse fromRedisFields(
            String jobId, String status, int fileId, String operation, String errorMessage, long createdMs, long updatedMs) {
        return new WatermarkJobResponse(
                jobId,
                status,
                fileId,
                operation,
                errorMessage == null || errorMessage.isBlank() ? null : errorMessage,
                Instant.ofEpochMilli(createdMs),
                Instant.ofEpochMilli(updatedMs));
    }
}

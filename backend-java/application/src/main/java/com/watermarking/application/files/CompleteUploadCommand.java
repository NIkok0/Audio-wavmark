package com.watermarking.application.files;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;

public record CompleteUploadCommand(
        @NotBlank String objectKey,
        @NotBlank String etag,
        @Positive long size,
        @NotBlank String filename,
        @NotBlank String mediaType) {}

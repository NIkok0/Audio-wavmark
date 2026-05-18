package com.watermarking.application.stats;

import java.time.Instant;

public record FileSummaryDto(Integer id, String filename, String fileType, long fileSize, Instant createdAt) {}

package com.watermarking.application.stats;

import java.util.List;

public record GlobalDashboardDto(
        long totalFiles,
        long totalSizeBytes,
        String totalSizeHuman,
        long watermarkedCount,
        long nonWatermarkedCount,
        List<String> typeLabels,
        List<Long> typeValues,
        List<String> timeseriesLabels,
        List<Long> timeseriesCounts,
        List<FileSummaryDto> recentFiles) {}

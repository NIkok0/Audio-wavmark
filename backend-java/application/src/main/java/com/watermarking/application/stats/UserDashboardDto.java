package com.watermarking.application.stats;

import java.util.List;

public record UserDashboardDto(
        long total,
        long watermarked,
        long nonWatermarked,
        String totalSizeHuman,
        List<String> typeLabels,
        List<Long> typeValues,
        List<String> timeseriesLabels,
        List<Long> timeseriesCounts,
        List<FileSummaryDto> recentFiles) {}

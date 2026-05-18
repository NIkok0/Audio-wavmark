package com.watermarking.application.stats;

import com.watermarking.domain.model.File;
import com.watermarking.infrastructure.persistence.FileRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class DashboardStatsService {

    private static final List<String> TYPE_ORDER = List.of("image", "audio", "video", "text");
    private static final List<String> TYPE_LABELS_ZH = List.of("图片", "音频", "视频", "文档");
    private static final int SERIES_DAYS = 14;
    private static final DateTimeFormatter MM_DD = DateTimeFormatter.ofPattern("MM-dd");

    private final FileRepository fileRepository;

    public DashboardStatsService(FileRepository fileRepository) {
        this.fileRepository = fileRepository;
    }

    @Transactional(readOnly = true)
    public DashboardStatsResponse buildDashboard(Integer userIdOrNull) {
        GlobalDashboardDto global = buildGlobal();
        UserDashboardDto user = userIdOrNull == null ? null : buildUser(userIdOrNull);
        return new DashboardStatsResponse(global, user);
    }

    private GlobalDashboardDto buildGlobal() {
        long total = fileRepository.count();
        long sum = fileRepository.sumAllFileSizes();
        long wm = fileRepository.countWithWatermark();
        Map<String, Long> byType = toTypeMap(fileRepository.countGroupedByFileType());
        List<Long> typeValues = orderedValues(byType);
        Instant start = seriesStartInstant();
        Map<String, Long> dayCounts = toDayMap(fileRepository.countUploadsByDayGlobal(start));
        Series series = buildSeries(start, dayCounts);
        List<FileSummaryDto> recent = mapSummaries(
                fileRepository.findAll(PageRequest.of(0, 5, Sort.by(Sort.Direction.DESC, "createdAt"))).getContent());
        return new GlobalDashboardDto(
                total,
                sum,
                humanSize(sum),
                wm,
                Math.max(0, total - wm),
                TYPE_LABELS_ZH,
                typeValues,
                series.labels(),
                series.counts(),
                recent);
    }

    private UserDashboardDto buildUser(int uid) {
        long total = fileRepository.countForUploader(uid);
        long wm = fileRepository.countWithWatermarkForUploader(uid);
        long sum = fileRepository.sumFileSizesForUploader(uid);
        Map<String, Long> byType = toTypeMap(fileRepository.countGroupedByFileTypeForUploader(uid));
        List<Long> typeValues = orderedValues(byType);
        Instant start = seriesStartInstant();
        Map<String, Long> dayCounts = toDayMap(fileRepository.countUploadsByDayForUploader(uid, start));
        Series series = buildSeries(start, dayCounts);
        List<FileSummaryDto> recent =
                mapSummaries(fileRepository
                        .findByUploader_IdOrderByCreatedAtDesc(uid, PageRequest.of(0, 5, Sort.by(Sort.Direction.DESC, "createdAt")))
                        .getContent());
        return new UserDashboardDto(
                total,
                wm,
                Math.max(0, total - wm),
                humanSize(sum),
                TYPE_LABELS_ZH,
                typeValues,
                series.labels(),
                series.counts(),
                recent);
    }

    private static Instant seriesStartInstant() {
        LocalDate startDay = LocalDate.now(ZoneOffset.UTC).minusDays(SERIES_DAYS - 1L);
        return startDay.atStartOfDay(ZoneOffset.UTC).toInstant();
    }

    private record Series(List<String> labels, List<Long> counts) {}

    private Series buildSeries(Instant start, Map<String, Long> dayCounts) {
        List<String> labels = new ArrayList<>(SERIES_DAYS);
        List<Long> counts = new ArrayList<>(SERIES_DAYS);
        LocalDate d = LocalDate.ofInstant(start, ZoneOffset.UTC);
        for (int i = 0; i < SERIES_DAYS; i++) {
            labels.add(d.format(MM_DD));
            counts.add(dayCounts.getOrDefault(d.toString(), 0L));
            d = d.plusDays(1);
        }
        return new Series(labels, counts);
    }

    private static Map<String, Long> toTypeMap(List<Object[]> rows) {
        Map<String, Long> m = new HashMap<>();
        if (rows == null) {
            return m;
        }
        for (Object[] row : rows) {
            if (row == null || row.length < 2 || row[0] == null) {
                continue;
            }
            m.put(String.valueOf(row[0]), ((Number) row[1]).longValue());
        }
        return m;
    }

    private static Map<String, Long> toDayMap(List<Object[]> rows) {
        Map<String, Long> m = new HashMap<>();
        if (rows == null) {
            return m;
        }
        for (Object[] row : rows) {
            if (row == null || row.length < 2 || row[0] == null) {
                continue;
            }
            String dayKey = dayKeyFromSql(row[0]);
            m.put(dayKey, ((Number) row[1]).longValue());
        }
        return m;
    }

    private static String dayKeyFromSql(Object sqlDate) {
        if (sqlDate instanceof java.sql.Date d) {
            return d.toLocalDate().toString();
        }
        if (sqlDate instanceof java.time.LocalDate ld) {
            return ld.toString();
        }
        return String.valueOf(sqlDate).substring(0, Math.min(10, String.valueOf(sqlDate).length()));
    }

    private static List<Long> orderedValues(Map<String, Long> byType) {
        List<Long> out = new ArrayList<>(4);
        for (String t : TYPE_ORDER) {
            out.add(byType.getOrDefault(t, 0L));
        }
        return out;
    }

    private static List<FileSummaryDto> mapSummaries(List<File> files) {
        if (files == null) {
            return List.of();
        }
        return files.stream()
                .map(f -> new FileSummaryDto(
                        f.getId(), f.getFilename(), f.getFileType(), f.getFileSize(), f.getCreatedAt()))
                .toList();
    }

    static String humanSize(long bytes) {
        if (bytes < 1024) {
            return bytes + " B";
        }
        double kb = bytes / 1024.0;
        if (kb < 1024) {
            return String.format("%.1f KB", kb);
        }
        double mb = kb / 1024.0;
        if (mb < 1024) {
            return String.format("%.1f MB", mb);
        }
        return String.format("%.2f GB", mb / 1024.0);
    }
}

package com.watermarking.application.retention;

import com.watermarking.application.files.FileService;
import com.watermarking.domain.model.File;
import com.watermarking.domain.model.User;
import com.watermarking.infrastructure.config.WmRetentionProperties;
import com.watermarking.infrastructure.persistence.FileRepository;
import com.watermarking.infrastructure.persistence.UserRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.List;

/**
 * 按用户 {@code retention_days}（缺省见配置）删除过期 {@link File} 行与物理对象；与 Flask 后台线程语义一致。
 */
@Service
public class RetentionCleanupService {

    private static final Logger log = LoggerFactory.getLogger(RetentionCleanupService.class);

    private final UserRepository userRepository;
    private final FileRepository fileRepository;
    private final FileService fileService;
    private final WmRetentionProperties retentionProperties;

    public RetentionCleanupService(
            UserRepository userRepository,
            FileRepository fileRepository,
            FileService fileService,
            WmRetentionProperties retentionProperties) {
        this.userRepository = userRepository;
        this.fileRepository = fileRepository;
        this.fileService = fileService;
        this.retentionProperties = retentionProperties;
    }

    public void runOnce() {
        int def = Math.max(1, retentionProperties.getDefaultRetentionDays());
        List<User> users = userRepository.findAll();
        for (User u : users) {
            int days = u.getRetentionDays() != null && u.getRetentionDays() > 0 ? u.getRetentionDays() : def;
            Instant cutoff = Instant.now().minus(days, ChronoUnit.DAYS);
            List<File> stale = fileRepository.findByUploader_IdAndCreatedAtBefore(u.getId(), cutoff);
            if (stale.isEmpty()) {
                continue;
            }
            int removed = 0;
            for (File f : stale) {
                try {
                    fileService.deleteByIdForSystemRetention(f.getId());
                    removed++;
                } catch (IOException e) {
                    log.warn("retention delete failed fileId={} userId={}: {}", f.getId(), u.getId(), e.getMessage());
                } catch (RuntimeException e) {
                    log.warn("retention delete failed fileId={} userId={}: {}", f.getId(), u.getId(), e.getMessage());
                }
            }
            if (removed > 0) {
                log.info("retention cleanup user={} days={} removed={}", u.getUsername(), days, removed);
            }
        }
    }
}

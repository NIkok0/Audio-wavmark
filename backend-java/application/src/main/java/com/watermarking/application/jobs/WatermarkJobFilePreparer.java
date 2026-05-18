package com.watermarking.application.jobs;

import com.watermarking.application.files.StoredFileNotFoundException;
import com.watermarking.domain.model.File;
import com.watermarking.infrastructure.persistence.FileRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class WatermarkJobFilePreparer {

    private final FileRepository fileRepository;

    public WatermarkJobFilePreparer(FileRepository fileRepository) {
        this.fileRepository = fileRepository;
    }

    @Transactional
    public File markProcessing(int userId, CreateWatermarkJobRequest req) {
        File f = fileRepository
                .findByIdAndUploader_Id(req.getFileId(), userId)
                .orElseThrow(() -> new StoredFileNotFoundException("文件不存在"));
        if (f.isHasWatermark()) {
            throw new InvalidWatermarkJobStateException("该文件已含有水印版本");
        }
        String ps = f.getProcessingStatus();
        if ("processing".equals(ps)) {
            throw new InvalidWatermarkJobStateException("该文件已有进行中的水印任务");
        }
        if (!List.of("pending", "failed").contains(ps)) {
            throw new InvalidWatermarkJobStateException("当前处理状态不可再次入队: " + ps);
        }
        f.setWatermarkText(req.getWatermarkText());
        if (req.getWatermarkSeed() != null && !req.getWatermarkSeed().isBlank()) {
            f.setWatermarkSeed(req.getWatermarkSeed());
        } else {
            f.setWatermarkSeed(null);
        }
        if (req.getAlgorithm() != null && !req.getAlgorithm().isBlank()) {
            f.setWatermarkType(req.getAlgorithm());
        }
        f.setProcessingStatus("processing");
        f.setErrorMessage(null);
        return fileRepository.save(f);
    }
}

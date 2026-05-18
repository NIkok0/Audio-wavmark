package com.watermarking.application.jobs;

import com.watermarking.domain.model.File;
import com.watermarking.infrastructure.persistence.FileRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

@Service
public class JobEnqueueRecoveryService {

    private final FileRepository fileRepository;

    public JobEnqueueRecoveryService(FileRepository fileRepository) {
        this.fileRepository = fileRepository;
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void revertFileToPendingAfterEnqueueFailure(int fileId, int userId, String message) {
        File f = fileRepository.findByIdAndUploader_Id(fileId, userId).orElse(null);
        if (f == null) {
            return;
        }
        if ("processing".equals(f.getProcessingStatus())) {
            f.setProcessingStatus("pending");
            f.setErrorMessage(message);
            fileRepository.save(f);
        }
    }
}

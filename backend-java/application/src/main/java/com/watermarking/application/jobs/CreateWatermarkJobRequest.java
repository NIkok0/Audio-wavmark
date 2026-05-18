package com.watermarking.application.jobs;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

/**
 * {@code POST /api/v1/jobs/watermark} 请求体；当前仅支持嵌入（与队列 {@code operation} 固定为 embed 一致）。
 */
public class CreateWatermarkJobRequest {

    @NotNull
    private Integer fileId;

    @NotBlank
    private String watermarkText;

    private String watermarkSeed;

    /** 可选；写入 {@code files.watermark_type}，Worker 侧 {@code AlgorithmSelector} 仍可自动选择 */
    private String algorithm;

    public Integer getFileId() {
        return fileId;
    }

    public void setFileId(Integer fileId) {
        this.fileId = fileId;
    }

    public String getWatermarkText() {
        return watermarkText;
    }

    public void setWatermarkText(String watermarkText) {
        this.watermarkText = watermarkText;
    }

    public String getWatermarkSeed() {
        return watermarkSeed;
    }

    public void setWatermarkSeed(String watermarkSeed) {
        this.watermarkSeed = watermarkSeed;
    }

    public String getAlgorithm() {
        return algorithm;
    }

    public void setAlgorithm(String algorithm) {
        this.algorithm = algorithm;
    }
}

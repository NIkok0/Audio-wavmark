package com.watermarking.domain.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreUpdate;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "files")
public class File {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(nullable = false, length = 255)
    private String filename;

    @Column(name = "original_path", nullable = false, length = 512)
    private String originalPath;

    @Column(name = "watermarked_path", length = 512)
    private String watermarkedPath;

    @Column(name = "file_hash", nullable = false, length = 128)
    private String fileHash;

    @Column(name = "file_watermark_hash", length = 128)
    private String fileWatermarkHash;

    @Column(name = "has_watermark", nullable = false)
    private boolean hasWatermark = false;

    @Column(name = "file_type", nullable = false, length = 20)
    private String fileType;

    @Column(name = "file_format", nullable = false, length = 20)
    private String fileFormat;

    @Column(name = "file_size", nullable = false)
    private long fileSize;

    @Column(name = "mime_type", nullable = false, length = 100)
    private String mimeType;

    @Column(name = "watermark_type", length = 50)
    private String watermarkType;

    @Column(name = "watermark_text", columnDefinition = "TEXT")
    private String watermarkText;

    @Column(name = "original_watermark_text", columnDefinition = "TEXT")
    private String originalWatermarkText;

    @Column(name = "watermark_seed", length = 20)
    private String watermarkSeed;

    @Column(name = "processing_status", nullable = false, length = 20)
    private String processingStatus = "pending";

    @Column(name = "error_message", columnDefinition = "TEXT")
    private String errorMessage;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "uploader_id", nullable = false)
    private User uploader;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "group_id")
    private Group group;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    @PrePersist
    void prePersist() {
        Instant now = Instant.now();
        if (createdAt == null) {
            createdAt = now;
        }
        updatedAt = now;
    }

    @PreUpdate
    void preUpdate() {
        updatedAt = Instant.now();
    }

    public Integer getId() {
        return id;
    }

    public void setId(Integer id) {
        this.id = id;
    }

    public String getFilename() {
        return filename;
    }

    public void setFilename(String filename) {
        this.filename = filename;
    }

    public String getOriginalPath() {
        return originalPath;
    }

    public void setOriginalPath(String originalPath) {
        this.originalPath = originalPath;
    }

    public String getWatermarkedPath() {
        return watermarkedPath;
    }

    public void setWatermarkedPath(String watermarkedPath) {
        this.watermarkedPath = watermarkedPath;
    }

    public String getFileHash() {
        return fileHash;
    }

    public void setFileHash(String fileHash) {
        this.fileHash = fileHash;
    }

    public String getFileWatermarkHash() {
        return fileWatermarkHash;
    }

    public void setFileWatermarkHash(String fileWatermarkHash) {
        this.fileWatermarkHash = fileWatermarkHash;
    }

    public boolean isHasWatermark() {
        return hasWatermark;
    }

    public void setHasWatermark(boolean hasWatermark) {
        this.hasWatermark = hasWatermark;
    }

    public String getFileType() {
        return fileType;
    }

    public void setFileType(String fileType) {
        this.fileType = fileType;
    }

    public String getFileFormat() {
        return fileFormat;
    }

    public void setFileFormat(String fileFormat) {
        this.fileFormat = fileFormat;
    }

    public long getFileSize() {
        return fileSize;
    }

    public void setFileSize(long fileSize) {
        this.fileSize = fileSize;
    }

    public String getMimeType() {
        return mimeType;
    }

    public void setMimeType(String mimeType) {
        this.mimeType = mimeType;
    }

    public String getWatermarkType() {
        return watermarkType;
    }

    public void setWatermarkType(String watermarkType) {
        this.watermarkType = watermarkType;
    }

    public String getWatermarkText() {
        return watermarkText;
    }

    public void setWatermarkText(String watermarkText) {
        this.watermarkText = watermarkText;
    }

    public String getOriginalWatermarkText() {
        return originalWatermarkText;
    }

    public void setOriginalWatermarkText(String originalWatermarkText) {
        this.originalWatermarkText = originalWatermarkText;
    }

    public String getWatermarkSeed() {
        return watermarkSeed;
    }

    public void setWatermarkSeed(String watermarkSeed) {
        this.watermarkSeed = watermarkSeed;
    }

    public String getProcessingStatus() {
        return processingStatus;
    }

    public void setProcessingStatus(String processingStatus) {
        this.processingStatus = processingStatus;
    }

    public String getErrorMessage() {
        return errorMessage;
    }

    public void setErrorMessage(String errorMessage) {
        this.errorMessage = errorMessage;
    }

    public User getUploader() {
        return uploader;
    }

    public void setUploader(User uploader) {
        this.uploader = uploader;
    }

    public Group getGroup() {
        return group;
    }

    public void setGroup(Group group) {
        this.group = group;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(Instant createdAt) {
        this.createdAt = createdAt;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(Instant updatedAt) {
        this.updatedAt = updatedAt;
    }
}

-- 保留期清理按 uploader + created_at 扫描
CREATE INDEX idx_files_uploader_created ON files (uploader_id, created_at);

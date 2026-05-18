-- Aligned with watermark/watermark/models.py (Flask SQLAlchemy)

CREATE TABLE users (
    id INT NOT NULL AUTO_INCREMENT,
    username VARCHAR(64) NOT NULL,
    email VARCHAR(64) NOT NULL,
    password VARCHAR(512) NOT NULL,
    is_admin TINYINT(1) NOT NULL DEFAULT 0,
    role VARCHAR(20) NOT NULL DEFAULT 'member',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    is_embed TINYINT(1) NOT NULL DEFAULT 1,
    is_extract TINYINT(1) NOT NULL DEFAULT 1,
    retention_days INT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_users_username (username),
    UNIQUE KEY uk_users_email (email),
    KEY idx_users_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `groups` (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(64) NOT NULL,
    description TEXT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uk_groups_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE user_group_rel (
    user_id INT NOT NULL,
    group_id INT NOT NULL,
    PRIMARY KEY (user_id, group_id),
    CONSTRAINT fk_user_group_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_user_group_group FOREIGN KEY (group_id) REFERENCES `groups` (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE files (
    id INT NOT NULL AUTO_INCREMENT,
    filename VARCHAR(255) NOT NULL,
    original_path VARCHAR(512) NOT NULL,
    watermarked_path VARCHAR(512) NULL,
    file_hash VARCHAR(128) NOT NULL,
    file_watermark_hash VARCHAR(128) NULL,
    has_watermark TINYINT(1) NOT NULL DEFAULT 0,
    file_type VARCHAR(20) NOT NULL,
    file_format VARCHAR(20) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    watermark_type VARCHAR(50) NULL,
    watermark_text TEXT NULL,
    original_watermark_text TEXT NULL,
    watermark_seed VARCHAR(20) NULL,
    processing_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    error_message TEXT NULL,
    uploader_id INT NOT NULL,
    group_id INT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY idx_files_uploader (uploader_id),
    KEY idx_files_group (group_id),
    KEY idx_files_status (processing_status),
    CONSTRAINT fk_files_uploader FOREIGN KEY (uploader_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_files_group FOREIGN KEY (group_id) REFERENCES `groups` (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

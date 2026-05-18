package com.watermarking.application.admin;

/**
 * 对齐 Flask 权限管理页统计卡片：用户数、活跃、管理员数、组数（范围与 {@code GET /api/v1/admin/users} 一致）。
 */
public record AdminStatsResponse(long totalUsers, long activeUsers, long adminUsers, long totalGroups) {}

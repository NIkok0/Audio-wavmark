package com.watermarking.application.admin;

import com.watermarking.domain.model.User;

import java.time.Instant;
import java.util.Set;
import java.util.stream.Collectors;

public record AdminUserResponse(
        int id,
        String username,
        String email,
        String role,
        boolean admin,
        boolean active,
        boolean embed,
        boolean extract,
        Integer retentionDays,
        Set<Integer> groupIds,
        Instant createdAt,
        Instant updatedAt) {

    public static AdminUserResponse fromEntity(User u) {
        Set<Integer> gids = u.getGroups().stream().map(g -> g.getId()).collect(Collectors.toSet());
        return new AdminUserResponse(
                u.getId(),
                u.getUsername(),
                u.getEmail(),
                u.getRole(),
                u.isAdmin(),
                u.isActive(),
                u.isEmbed(),
                u.isExtract(),
                u.getRetentionDays(),
                gids,
                u.getCreatedAt(),
                u.getUpdatedAt());
    }
}

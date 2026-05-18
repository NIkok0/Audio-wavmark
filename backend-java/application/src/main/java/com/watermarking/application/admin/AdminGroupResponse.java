package com.watermarking.application.admin;

import com.watermarking.domain.model.Group;

import java.time.Instant;

public record AdminGroupResponse(int id, String name, String description, Instant createdAt) {

    public static AdminGroupResponse fromEntity(Group g) {
        return new AdminGroupResponse(g.getId(), g.getName(), g.getDescription(), g.getCreatedAt());
    }
}

package com.watermarking.application.admin;

import jakarta.validation.constraints.NotEmpty;

import java.util.List;

public class AdminBatchDeleteUsersRequest {

    @NotEmpty
    private List<Integer> userIds;

    public List<Integer> getUserIds() {
        return userIds;
    }

    public void setUserIds(List<Integer> userIds) {
        this.userIds = userIds;
    }
}

package com.watermarking.application.admin;

import java.util.List;

public record PagedAdminUsersResponse(List<AdminUserResponse> content, long totalElements, int page, int size) {}

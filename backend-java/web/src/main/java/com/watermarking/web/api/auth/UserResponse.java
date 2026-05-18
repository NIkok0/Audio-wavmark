package com.watermarking.web.api.auth;

import com.watermarking.domain.model.User;
import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "当前用户摘要（不含密码）")
public record UserResponse(
        @Schema(description = "用户 ID") Integer id,
        @Schema(description = "用户名") String username,
        @Schema(description = "邮箱") String email,
        @Schema(description = "角色：super_admin / admin / member") String role,
        @Schema(description = "是否管理员标记（历史字段）") boolean admin,
        @Schema(description = "账户是否启用") boolean active) {

    static UserResponse from(User user) {
        return new UserResponse(
                user.getId(),
                user.getUsername(),
                user.getEmail(),
                user.getRole(),
                user.isAdmin(),
                user.isActive());
    }
}

package com.watermarking.web.api.auth;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "登录请求（用户名或邮箱 + 密码）；空字段错误与 Flask 一致，由接口层校验")
public record LoginRequest(
        @Schema(description = "用户名或邮箱") String usernameOrEmail,
        @Schema(description = "密码") String password) {
}

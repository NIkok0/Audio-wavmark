package com.watermarking.web.api.auth;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

@Schema(description = "注册请求")
public record RegisterRequest(
        @NotBlank @Size(min = 3, max = 64) @Schema(description = "用户名", example = "alice") String username,
        @NotBlank @Email @Size(max = 64) @Schema(description = "邮箱", example = "alice@example.com") String email,
        @NotBlank @Size(min = 6) @Schema(description = "密码", minLength = 6) String password) {
}

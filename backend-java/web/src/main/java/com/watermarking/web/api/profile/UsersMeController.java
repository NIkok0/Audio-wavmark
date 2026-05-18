package com.watermarking.web.api.profile;

import com.watermarking.application.auth.DomainUserDetails;
import com.watermarking.application.profile.PatchRetentionRequest;
import com.watermarking.application.profile.UserProfileService;
import com.watermarking.domain.model.User;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/users/me")
@Tag(name = "Current user", description = "当前登录用户设置")
public class UsersMeController {

    private final UserProfileService userProfileService;

    public UsersMeController(UserProfileService userProfileService) {
        this.userProfileService = userProfileService;
    }

    @PatchMapping("/retention")
    @Operation(summary = "更新文件保留天数", description = "与 Flask {@code /api/profile/retention} 一致，范围 1–365。")
    public ResponseEntity<Void> patchRetention(@Valid @RequestBody PatchRetentionRequest body) {
        User user = currentUser();
        userProfileService.updateRetentionDays(user.getId(), body);
        return ResponseEntity.noContent().build();
    }

    private static User currentUser() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || !(auth.getPrincipal() instanceof DomainUserDetails details)) {
            throw new AccessDeniedException("需要登录");
        }
        return details.getUser();
    }
}

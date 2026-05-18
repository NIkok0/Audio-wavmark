package com.watermarking.web.api.admin;

import com.watermarking.application.admin.AdminGroupResponse;
import com.watermarking.application.admin.AdminGroupService;
import com.watermarking.application.auth.DomainUserDetails;
import com.watermarking.domain.model.User;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/v1/admin/groups")
@Tag(name = "Admin groups", description = "用户组列表（超级管理员看全部；普通管理员仅看自己所在组）")
public class AdminGroupsController {

    private final AdminGroupService adminGroupService;

    public AdminGroupsController(AdminGroupService adminGroupService) {
        this.adminGroupService = adminGroupService;
    }

    @GetMapping
    @Operation(summary = "列出组", description = "供权限管理界面与组分配使用。")
    public List<AdminGroupResponse> list() {
        return adminGroupService.list(currentUser());
    }

    private static User currentUser() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || !(auth.getPrincipal() instanceof DomainUserDetails details)) {
            throw new AccessDeniedException("需要登录");
        }
        return details.getUser();
    }
}

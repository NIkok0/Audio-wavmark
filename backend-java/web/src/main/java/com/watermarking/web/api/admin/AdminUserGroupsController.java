package com.watermarking.web.api.admin;

import com.watermarking.application.admin.AdminUserGroupService;
import com.watermarking.application.admin.AdminUserResponse;
import com.watermarking.application.auth.DomainUserDetails;
import com.watermarking.domain.model.User;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/admin/users/{userId}/groups")
@Tag(name = "Admin user groups", description = "用户与组的关联（对齐 Flask 后台组分配）")
public class AdminUserGroupsController {

    private final AdminUserGroupService adminUserGroupService;

    public AdminUserGroupsController(AdminUserGroupService adminUserGroupService) {
        this.adminUserGroupService = adminUserGroupService;
    }

    @PostMapping("/{groupId}")
    @Operation(summary = "将用户加入组", description = "普通管理员仅可把自己管辖范围内的用户加入自己所在的组。")
    public ResponseEntity<AdminUserResponse> add(
            @PathVariable("userId") int userId, @PathVariable("groupId") int groupId) {
        AdminUserResponse body = adminUserGroupService.addUserToGroup(currentUser(), userId, groupId);
        return ResponseEntity.status(HttpStatus.OK).body(body);
    }

    @DeleteMapping("/{groupId}")
    @Operation(summary = "将用户移出组")
    public AdminUserResponse remove(@PathVariable("userId") int userId, @PathVariable("groupId") int groupId) {
        return adminUserGroupService.removeUserFromGroup(currentUser(), userId, groupId);
    }

    private static User currentUser() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || !(auth.getPrincipal() instanceof DomainUserDetails details)) {
            throw new AccessDeniedException("需要登录");
        }
        return details.getUser();
    }
}

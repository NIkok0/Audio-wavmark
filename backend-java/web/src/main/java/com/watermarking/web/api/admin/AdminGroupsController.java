package com.watermarking.web.api.admin;

import com.watermarking.application.admin.AdminGroupRequest;
import com.watermarking.application.admin.AdminGroupResponse;
import com.watermarking.application.admin.AdminGroupService;
import com.watermarking.application.auth.DomainUserDetails;
import com.watermarking.domain.model.User;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
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

    @PostMapping
    @Operation(summary = "创建组", description = "仅超级管理员可创建组。")
    public ResponseEntity<AdminGroupResponse> create(@Valid @RequestBody AdminGroupRequest body) {
        return ResponseEntity.status(HttpStatus.CREATED).body(adminGroupService.create(currentUser(), body));
    }

    @PatchMapping("/{id}")
    @Operation(summary = "编辑组", description = "仅超级管理员可编辑组。")
    public AdminGroupResponse patch(@PathVariable("id") int id, @Valid @RequestBody AdminGroupRequest body) {
        return adminGroupService.patch(currentUser(), id, body);
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除组", description = "仅超级管理员可删除组。")
    public ResponseEntity<Void> delete(@PathVariable("id") int id) {
        adminGroupService.delete(currentUser(), id);
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

package com.watermarking.web.api.admin;

import com.watermarking.application.admin.AdminBatchDeleteUsersRequest;
import com.watermarking.application.admin.AdminCreateUserRequest;
import com.watermarking.application.admin.AdminPatchUserRequest;
import com.watermarking.application.admin.AdminUserResponse;
import com.watermarking.application.admin.AdminUserService;
import com.watermarking.application.admin.PagedAdminUsersResponse;
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
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 对齐 Flask {@code /admin/*} 权限管理：{@code super_admin} 全量，{@code admin} 仅同组用户。
 */
@RestController
@RequestMapping("/api/v1/admin/users")
@Tag(name = "Admin users", description = "管理员用户列表、详情、创建与部分更新（需 admin/super_admin）")
public class AdminUsersController {

    private final AdminUserService adminUserService;

    public AdminUsersController(AdminUserService adminUserService) {
        this.adminUserService = adminUserService;
    }

    @GetMapping
    @Operation(summary = "分页查询用户", description = "支持 username/email 模糊搜索；普通管理员仅见同组用户。")
    public PagedAdminUsersResponse list(
            @RequestParam(required = false) String search,
            @RequestParam(required = false) String role,
            @RequestParam(required = false) Boolean active,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        User viewer = currentUser();
        return adminUserService.list(viewer, search, role, active, page, size);
    }

    @GetMapping("/{id}")
    @Operation(summary = "用户详情")
    public AdminUserResponse get(@PathVariable("id") int id) {
        User viewer = currentUser();
        return adminUserService.get(viewer, id);
    }

    @PostMapping
    @Operation(summary = "创建用户", description = "仅超级管理员可将角色设为 super_admin。")
    public ResponseEntity<AdminUserResponse> create(@Valid @RequestBody AdminCreateUserRequest body) {
        User viewer = currentUser();
        AdminUserResponse created = adminUserService.create(viewer, body);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }

    @PatchMapping("/{id}")
    @Operation(summary = "部分更新用户", description = "不能编辑自己；普通管理员不可操作系统超级管理员。")
    public AdminUserResponse patch(@PathVariable("id") int id, @Valid @RequestBody AdminPatchUserRequest body) {
        User viewer = currentUser();
        return adminUserService.patch(viewer, id, body);
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除用户", description = "仅超级管理员可删除，且不能删除当前登录用户。")
    public ResponseEntity<Void> delete(@PathVariable("id") int id) {
        adminUserService.delete(currentUser(), id);
        return ResponseEntity.noContent().build();
    }

    @PostMapping("/batch-delete")
    @Operation(summary = "批量删除用户", description = "仅超级管理员可批量删除用户。")
    public ResponseEntity<Void> batchDelete(@Valid @RequestBody AdminBatchDeleteUsersRequest body) {
        adminUserService.batchDelete(currentUser(), body.getUserIds());
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

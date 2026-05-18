package com.watermarking.web.api.admin;

import com.watermarking.application.admin.AdminStatsResponse;
import com.watermarking.application.admin.AdminStatisticsService;
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

@RestController
@RequestMapping("/api/v1/admin/stats")
@Tag(name = "Admin statistics", description = "管理端仪表盘计数（与 Flask 权限管理页统计一致）")
public class AdminStatisticsController {

    private final AdminStatisticsService adminStatisticsService;

    public AdminStatisticsController(AdminStatisticsService adminStatisticsService) {
        this.adminStatisticsService = adminStatisticsService;
    }

    @GetMapping
    @Operation(
            summary = "用户与组统计",
            description =
                    "在 `GET /api/v1/admin/users` 相同范围内统计：总用户、活跃用户、管理员（admin+super_admin）数量；"
                            + "组数为超管下全库组数，普通管理员为其所在组个数。")
    public AdminStatsResponse get() {
        return adminStatisticsService.stats(currentUser());
    }

    private static User currentUser() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || !(auth.getPrincipal() instanceof DomainUserDetails details)) {
            throw new AccessDeniedException("需要登录");
        }
        return details.getUser();
    }
}

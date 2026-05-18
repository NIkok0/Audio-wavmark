package com.watermarking.web.api.stats;

import com.watermarking.application.auth.DomainUserDetails;
import com.watermarking.application.stats.DashboardStatsResponse;
import com.watermarking.application.stats.DashboardStatsService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/stats")
@Tag(name = "Stats", description = "首页仪表盘等统计 JSON")
public class StatsController {

    private final DashboardStatsService dashboardStatsService;

    public StatsController(DashboardStatsService dashboardStatsService) {
        this.dashboardStatsService = dashboardStatsService;
    }

    @GetMapping("/dashboard")
    @Operation(
            summary = "仪表盘数据",
            description = "匿名仅返回全站汇总；登录后额外返回当前用户汇总（与 Flask 首页统计口径一致）。")
    public DashboardStatsResponse dashboard(Authentication authentication) {
        Integer userId = null;
        if (authentication != null && authentication.getPrincipal() instanceof DomainUserDetails details) {
            userId = details.getUser().getId();
        }
        return dashboardStatsService.buildDashboard(userId);
    }
}

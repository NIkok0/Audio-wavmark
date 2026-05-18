package com.watermarking.web.api.jobs;

import com.watermarking.application.auth.DomainUserDetails;
import com.watermarking.application.jobs.CreateWatermarkJobRequest;
import com.watermarking.application.jobs.WatermarkJobResponse;
import com.watermarking.application.jobs.WatermarkJobService;
import com.watermarking.domain.model.User;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 阶段 4：异步水印任务入队（Redis Streams）与任务态查询。
 */
@RestController
@RequestMapping("/api/v1/jobs")
@Tag(name = "Jobs", description = "水印异步任务：入队与状态（Redis Hash）")
public class JobsController {

    private final WatermarkJobService watermarkJobService;

    public JobsController(WatermarkJobService watermarkJobService) {
        this.watermarkJobService = watermarkJobService;
    }

    @PostMapping("/watermark")
    @Operation(
            summary = "提交嵌入水印任务",
            description =
                    "将任务写入 Redis Stream（默认 `wm:stream:watermark`），并在 `wm:job:{jobId}` 记录任务态。"
                            + "可选请求头 `Idempotency-Key`：同一用户下相同键 24h 内复用同一 `jobId`。"
                            + "队列消息 JSON 字段见 `docs/watermark-java-backend-tech-selection.md` §10.1。")
    public ResponseEntity<WatermarkJobResponse> enqueueWatermark(
            @Valid @RequestBody CreateWatermarkJobRequest body,
            @Parameter(description = "幂等键：与 userId 组合映射到 jobId")
                    @RequestHeader(value = "Idempotency-Key", required = false)
                    String idempotencyKey) {
        User user = currentUser();
        WatermarkJobResponse r = watermarkJobService.enqueue(user.getId(), body, idempotencyKey);
        return ResponseEntity.status(HttpStatus.ACCEPTED).body(r);
    }

    @GetMapping("/{id}")
    @Operation(summary = "查询任务状态", description = "读取 Redis `wm:job:{id}`；仅任务所属用户可访问。")
    public WatermarkJobResponse get(@PathVariable("id") String id) {
        User user = currentUser();
        return watermarkJobService.getForUser(user.getId(), id);
    }

    private static User currentUser() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || !(auth.getPrincipal() instanceof DomainUserDetails details)) {
            throw new AccessDeniedException("需要登录");
        }
        return details.getUser();
    }
}

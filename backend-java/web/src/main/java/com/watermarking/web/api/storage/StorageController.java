package com.watermarking.web.api.storage;

import com.watermarking.application.auth.DomainUserDetails;
import com.watermarking.application.storage.StorageStsApplicationService;
import com.watermarking.domain.model.User;
import com.tencentcloudapi.common.exception.TencentCloudSDKException;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 阶段 3：STS / 预签名，供前端直传 MinIO（S3 兼容）或 COS。
 */
@RestController
@RequestMapping("/api/v1/storage")
@Tag(name = "Storage", description = "对象存储 STS / 预签名直传")
public class StorageController {

    private final StorageStsApplicationService storageStsApplicationService;

    public StorageController(StorageStsApplicationService storageStsApplicationService) {
        this.storageStsApplicationService = storageStsApplicationService;
    }

    @PostMapping("/sts")
    @Operation(
            summary = "获取直传凭证或预签名",
            description =
                    "`backend=minio` 时返回 `putUrl`（S3 预签名 PUT）；`backend=cos` 时返回临时密钥与 `objectKey`，"
                            + "需在 `wm.storage.cos.policy-json` 中配置 CAM 策略，可使用占位符 `${objectKeyPrefix}`。")
    public ResponseEntity<StorageStsApplicationService.StsIssueResponse> sts(
            @Valid @RequestBody StorageStsApplicationService.StsIssueRequest body) throws TencentCloudSDKException {
        User user = currentUser();
        return ResponseEntity.ok(storageStsApplicationService.issue(body, user.getId()));
    }

    private static User currentUser() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || !(auth.getPrincipal() instanceof DomainUserDetails details)) {
            throw new AccessDeniedException("需要登录");
        }
        return details.getUser();
    }
}

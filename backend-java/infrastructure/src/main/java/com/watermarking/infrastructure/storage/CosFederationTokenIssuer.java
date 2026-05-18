package com.watermarking.infrastructure.storage;

import com.tencentcloudapi.common.Credential;
import com.tencentcloudapi.common.profile.ClientProfile;
import com.tencentcloudapi.common.profile.HttpProfile;
import com.tencentcloudapi.sts.v20180813.StsClient;
import com.tencentcloudapi.sts.v20180813.models.GetFederationTokenRequest;
import com.tencentcloudapi.sts.v20180813.models.GetFederationTokenResponse;
import org.springframework.stereotype.Component;

import java.util.UUID;

/**
 * 腾讯云 CAM {@code GetFederationToken}，供前端 COS SDK 直传；策略由配置提供，可含占位符 {@code ${objectKeyPrefix}}。
 */
@Component
public class CosFederationTokenIssuer {

    private final WmStorageProperties properties;

    public CosFederationTokenIssuer(WmStorageProperties properties) {
        this.properties = properties;
    }

    public CosStsCredentials issue(int userId, String objectKeyPrefix) {
        WmStorageProperties.Cos cos = properties.getCos();
        if (cos.getSecretId().isBlank() || cos.getSecretKey().isBlank() || cos.getPolicyJson().isBlank()) {
            throw new ObjectStorageUnavailableException("COS STS 未配置：请设置 wm.storage.cos.secret-id、secret-key、policy-json");
        }
        String policy = cos.getPolicyJson().replace("${objectKeyPrefix}", objectKeyPrefix);

        Credential cred = new Credential(cos.getSecretId(), cos.getSecretKey());
        HttpProfile httpProfile = new HttpProfile();
        httpProfile.setEndpoint("sts.tencentcloudapi.com");
        ClientProfile clientProfile = new ClientProfile();
        clientProfile.setHttpProfile(httpProfile);
        StsClient client = new StsClient(cred, cos.getRegion(), clientProfile);

        GetFederationTokenRequest req = new GetFederationTokenRequest();
        req.setName("wm-" + userId + "-" + UUID.randomUUID().toString().replace("-", "").substring(0, 12));
        req.setPolicy(policy);
        req.setDurationSeconds((long) cos.getStsDuration().getSeconds());

        try {
            GetFederationTokenResponse resp = client.GetFederationToken(req);
            com.tencentcloudapi.sts.v20180813.models.Credentials c = resp.getCredentials();
            long exp = resp.getExpiredTime() != null ? resp.getExpiredTime() : 0L;
            return new CosStsCredentials(
                    c.getTmpSecretId(),
                    c.getTmpSecretKey(),
                    c.getToken(),
                    exp,
                    cos.getRegion(),
                    cos.getBucket());
        } catch (com.tencentcloudapi.common.exception.TencentCloudSDKException e) {
            throw new ObjectStorageUnavailableException("COS STS 签发失败: " + e.getMessage(), e);
        }
    }

    public record CosStsCredentials(
            String tmpSecretId,
            String tmpSecretKey,
            String sessionToken,
            long expiredTime,
            String region,
            String bucket) {}
}

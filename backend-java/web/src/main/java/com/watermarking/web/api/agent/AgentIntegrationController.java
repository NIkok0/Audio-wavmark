package com.watermarking.web.api.agent;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.actuate.health.HealthEndpoint;
import org.springframework.boot.actuate.health.Status;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/v1/agent")
@Tag(name = "Agent Integration", description = "Discovery metadata for an external LearnAgent service")
public class AgentIntegrationController {

    private final HealthEndpoint healthEndpoint;
    private final String publicBaseUrl;
    private final String sessionCookieName;
    private final String learnAgentRepository;

    public AgentIntegrationController(
            HealthEndpoint healthEndpoint,
            @Value("${wm.agent.public-base-url:}") String publicBaseUrl,
            @Value("${server.servlet.session.cookie.name:WMSESSIONID}") String sessionCookieName,
            @Value("${wm.agent.learn-agent-repository:https://github.com/NIkok0/LearnAgent}") String learnAgentRepository) {
        this.healthEndpoint = healthEndpoint;
        this.publicBaseUrl = publicBaseUrl;
        this.sessionCookieName = sessionCookieName;
        this.learnAgentRepository = learnAgentRepository;
    }

    @GetMapping("/integration")
    @Operation(
            summary = "External agent integration metadata",
            description = "Returns stable API paths and session metadata for the standalone LearnAgent service.")
    public AgentIntegrationResponse integration() {
        boolean healthy = Status.UP.equals(healthEndpoint.health().getStatus());
        return new AgentIntegrationResponse(
                "watermark-api",
                healthy,
                blankToNull(publicBaseUrl),
                sessionCookieName,
                learnAgentRepository,
                "/actuator/health",
                List.of(
                        "GET /actuator/health",
                        "POST /api/v1/auth/login",
                        "GET /api/v1/stats/dashboard",
                        "GET /api/v1/files",
                        "GET /api/v1/files/{id}",
                        "GET /api/v1/jobs/{id}",
                        "GET /api/v1/admin/stats",
                        "GET /api/v1/admin/users",
                        "GET /api/v1/admin/groups",
                        "POST /api/v1/jobs/watermark (requires explicit external agent approval)"
                )
        );
    }

    private static String blankToNull(String value) {
        return value == null || value.isBlank() ? null : value;
    }

    public record AgentIntegrationResponse(
            String service,
            boolean healthy,
            String publicBaseUrl,
            String sessionCookieName,
            String learnAgentRepository,
            String healthPath,
            List<String> recommendedAllowlist
    ) {
    }
}

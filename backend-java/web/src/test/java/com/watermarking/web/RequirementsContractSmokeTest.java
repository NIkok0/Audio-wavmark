package com.watermarking.web;

import com.watermarking.application.auth.AuthService;
import com.watermarking.web.api.GlobalExceptionHandler;
import com.watermarking.web.api.auth.AuthController;
import com.watermarking.web.ui.HealthController;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.MediaType;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.web.context.SecurityContextRepository;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * 对照《选型》§9.2 / 《重构》§8：校验失败返回 RFC 7807 {@code ProblemDetail}。
 * 映射文档 {@code backend-java/docs/REQUIREMENTS-CHECKLIST-AND-TEST-CASES.md} §6（TC-AUTH-02、TC-OPS-01b）。
 */
@ExtendWith(MockitoExtension.class)
class RequirementsContractSmokeTest {

    @Mock
    private AuthService authService;

    @Mock
    private AuthenticationManager authenticationManager;

    @Mock
    private SecurityContextRepository securityContextRepository;

    private MockMvc mockMvc;

    @BeforeEach
    void setUp() {
        AuthController controller =
                new AuthController(authService, authenticationManager, securityContextRepository);
        mockMvc =
                MockMvcBuilders.standaloneSetup(controller)
                        .setControllerAdvice(new GlobalExceptionHandler())
                        .build();
    }

    @Test
    @DisplayName("TC-AUTH-02: 注册参数校验失败 → 400 ProblemDetail (urn:watermarking:validation)")
    void registerValidationReturnsProblemDetail() throws Exception {
        mockMvc.perform(
                        post("/api/v1/auth/register")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(
                                        """
                                        {"username":"ab","email":"not-an-email","password":"short"}
                                        """))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.title").value("Validation failed"))
                .andExpect(jsonPath("$.type").value("urn:watermarking:validation"))
                .andExpect(jsonPath("$.status").value(400));
    }

    @Test
    @DisplayName("TC-OPS-01b: GET /health → 200 OK 纯文本")
    void loadBalancerHealthReturnsPlainOk() throws Exception {
        MockMvc healthMvc = MockMvcBuilders.standaloneSetup(new HealthController()).build();
        healthMvc.perform(get("/health"))
                .andExpect(status().isOk())
                .andExpect(content().string("OK"));
    }
}

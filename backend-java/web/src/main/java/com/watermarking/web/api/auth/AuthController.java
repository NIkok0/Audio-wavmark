package com.watermarking.web.api.auth;

import com.watermarking.application.auth.AuthService;
import com.watermarking.application.auth.DomainUserDetails;
import com.watermarking.domain.model.User;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.DisabledException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.core.context.SecurityContext;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.context.SecurityContextHolderStrategy;
import org.springframework.security.web.context.SecurityContextRepository;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/auth")
@Tag(name = "Auth", description = "注册、登录、登出（对齐 Flask register / signin / signout）")
public class AuthController {

    private final AuthService authService;
    private final AuthenticationManager authenticationManager;
    private final SecurityContextRepository securityContextRepository;
    private final SecurityContextHolderStrategy securityContextHolderStrategy;

    public AuthController(
            AuthService authService,
            AuthenticationManager authenticationManager,
            SecurityContextRepository securityContextRepository) {
        this.authService = authService;
        this.authenticationManager = authenticationManager;
        this.securityContextRepository = securityContextRepository;
        this.securityContextHolderStrategy = SecurityContextHolder.getContextHolderStrategy();
    }

    @PostMapping("/register")
    @Operation(summary = "用户注册", description = "用户名 3–64 字符，邮箱合法，密码至少 6 位；与 Flask register 校验一致")
    public ResponseEntity<UserResponse> register(@Valid @RequestBody RegisterRequest request) {
        User user = authService.register(request.username(), request.email(), request.password());
        return ResponseEntity.status(HttpStatus.CREATED).body(UserResponse.from(user));
    }

    @PostMapping("/login")
    @Operation(summary = "登录", description = "支持用户名或邮箱 + 密码；建立服务端 Session（Redis）")
    public ResponseEntity<UserResponse> login(
            @RequestBody LoginRequest request,
            HttpServletRequest httpRequest,
            HttpServletResponse httpResponse) {
        if (request == null) {
            throw new LoginFieldsRequiredException();
        }
        String principal = request.usernameOrEmail() == null ? "" : request.usernameOrEmail().trim();
        String password = request.password() == null ? "" : request.password();
        if (principal.isEmpty() || password.isEmpty()) {
            throw new LoginFieldsRequiredException();
        }
        try {
            Authentication authentication = authenticationManager.authenticate(
                    new UsernamePasswordAuthenticationToken(principal, password));
            SecurityContext context = securityContextHolderStrategy.createEmptyContext();
            context.setAuthentication(authentication);
            securityContextHolderStrategy.setContext(context);
            securityContextRepository.saveContext(context, httpRequest, httpResponse);
            DomainUserDetails details = (DomainUserDetails) authentication.getPrincipal();
            authService.upgradeLegacyPasswordHashIfPresent(details.getUser().getId(), password);
        } catch (DisabledException e) {
            throw new AccountInactiveException();
        } catch (BadCredentialsException e) {
            throw new FlaskStyleBadCredentialsException();
        } catch (AuthenticationException e) {
            throw new FlaskStyleBadCredentialsException();
        }
        DomainUserDetails details =
                (DomainUserDetails) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        return ResponseEntity.ok(UserResponse.from(details.getUser()));
    }

    @PostMapping("/logout")
    @Operation(summary = "登出", description = "清除 Session；浏览器客户端需携带 CSRF（Cookie XSRF-TOKEN + 头 X-XSRF-TOKEN）")
    public ResponseEntity<Void> logout(HttpServletRequest request) {
        SecurityContextHolder.clearContext();
        var session = request.getSession(false);
        if (session != null) {
            session.invalidate();
        }
        return ResponseEntity.noContent().build();
    }
}

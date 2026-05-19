package com.watermarking.web.config;

import com.watermarking.application.auth.LegacyAwarePasswordEncoder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.context.HttpSessionSecurityContextRepository;
import org.springframework.security.web.context.SecurityContextRepository;
import org.springframework.security.web.csrf.CookieCsrfTokenRepository;
import org.springframework.security.web.util.matcher.AntPathRequestMatcher;
import org.springframework.web.cors.CorsConfigurationSource;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new LegacyAwarePasswordEncoder();
    }

    @Bean
    public AuthenticationManager authenticationManager(AuthenticationConfiguration configuration) throws Exception {
        return configuration.getAuthenticationManager();
    }

    @Bean
    public SecurityContextRepository securityContextRepository() {
        return new HttpSessionSecurityContextRepository();
    }

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http, CorsConfigurationSource corsConfigurationSource) throws Exception {
        http
                .cors(cors -> cors.configurationSource(corsConfigurationSource))
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers(HttpMethod.POST, "/api/v1/auth/register", "/api/v1/auth/login").permitAll()
                        .requestMatchers("/health").permitAll()
                        .requestMatchers(HttpMethod.GET, "/", "/signin", "/register").permitAll()
                        .requestMatchers("/css/**", "/js/**").permitAll()
                        .requestMatchers("/actuator/health", "/actuator/info", "/actuator/prometheus", "/actuator/metrics", "/actuator/metrics/**")
                                .permitAll()
                        .requestMatchers("/v3/api-docs/**", "/swagger-ui/**", "/swagger-ui.html").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/v1/stats/dashboard").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/v1/agent/integration").permitAll()
                        .requestMatchers(HttpMethod.GET, "/feedback").permitAll()
                        .requestMatchers(HttpMethod.POST, "/api/v1/auth/logout").authenticated()
                        .requestMatchers("/admin/**").hasRole("ADMIN")
                        .requestMatchers("/image/**", "/audio/**", "/video/**", "/text/**").authenticated()
                        .requestMatchers("/profile/**").authenticated()
                        .requestMatchers("/search").authenticated()
                        .requestMatchers("/api/v1/admin/**").hasRole("ADMIN")
                        .anyRequest().authenticated())
                .csrf(csrf -> csrf
                        .csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse())
                        .ignoringRequestMatchers(
                                new AntPathRequestMatcher("/api/v1/auth/login", "POST"),
                                new AntPathRequestMatcher("/api/v1/auth/register", "POST"),
                                new AntPathRequestMatcher("/api/v1/files", "POST"),
                                new AntPathRequestMatcher("/api/v1/files/*", "DELETE"),
                                new AntPathRequestMatcher("/api/v1/files/complete", "POST"),
                                new AntPathRequestMatcher("/api/v1/storage/sts", "POST"),
                                new AntPathRequestMatcher("/api/v1/jobs/watermark", "POST"),
                                new AntPathRequestMatcher("/api/v1/admin/users", "POST"),
                                new AntPathRequestMatcher("/api/v1/admin/users/*", "PATCH"),
                                new AntPathRequestMatcher("/api/v1/admin/users/*", "DELETE"),
                                new AntPathRequestMatcher("/api/v1/admin/users/batch-delete", "POST"),
                                new AntPathRequestMatcher("/api/v1/admin/groups", "POST"),
                                new AntPathRequestMatcher("/api/v1/admin/groups/*", "PATCH"),
                                new AntPathRequestMatcher("/api/v1/admin/groups/*", "DELETE"),
                                new AntPathRequestMatcher("/api/v1/admin/users/*/groups/*", "POST"),
                                new AntPathRequestMatcher("/api/v1/admin/users/*/groups/*", "DELETE"),
                                new AntPathRequestMatcher("/api/v1/users/me/retention", "PATCH")))
                .httpBasic(AbstractHttpConfigurer::disable)
                .formLogin(AbstractHttpConfigurer::disable);
        return http.build();
    }
}

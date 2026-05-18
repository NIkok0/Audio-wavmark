package com.watermarking.infrastructure.config;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@EnableConfigurationProperties(WmRateLimitProperties.class)
public class WmRateLimitConfig {}

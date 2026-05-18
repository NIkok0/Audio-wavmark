package com.watermarking.infrastructure.config;

import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

@Configuration
@EntityScan(basePackages = "com.watermarking.domain.model")
@EnableJpaRepositories(basePackages = "com.watermarking.infrastructure.persistence")
public class JpaConfig {
}

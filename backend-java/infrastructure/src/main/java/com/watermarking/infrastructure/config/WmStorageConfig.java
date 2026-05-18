package com.watermarking.infrastructure.config;

import com.watermarking.infrastructure.storage.WmStorageProperties;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@EnableConfigurationProperties(WmStorageProperties.class)
public class WmStorageConfig {
}

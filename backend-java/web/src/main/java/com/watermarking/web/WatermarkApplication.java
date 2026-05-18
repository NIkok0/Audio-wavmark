package com.watermarking.web;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
@ComponentScan(basePackages = {
        "com.watermarking.web",
        "com.watermarking.application",
        "com.watermarking.infrastructure"
})
public class WatermarkApplication {

    public static void main(String[] args) {
        SpringApplication.run(WatermarkApplication.class, args);
    }
}

package com.watermarking.application.admin;

public class AdminUserNotFoundException extends RuntimeException {

    public AdminUserNotFoundException(String message) {
        super(message);
    }
}

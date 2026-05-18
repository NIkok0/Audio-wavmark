package com.watermarking.web.api.auth;

public class AccountInactiveException extends RuntimeException {

    public AccountInactiveException() {
        super("账户已禁用，请联系管理员。");
    }
}

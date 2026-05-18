package com.watermarking.web.api.auth;

/**
 * Maps to the Flask signin empty-field message.
 */
public class LoginFieldsRequiredException extends RuntimeException {

    public LoginFieldsRequiredException() {
        super("请填写用户名和密码！");
    }
}

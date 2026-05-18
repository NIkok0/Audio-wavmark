package com.watermarking.web.api.auth;

/**
 * Maps to the Flask signin wrong-password message.
 */
public class FlaskStyleBadCredentialsException extends RuntimeException {

    public FlaskStyleBadCredentialsException() {
        super("用户名/邮箱或密码错误，请重新登录！");
    }
}

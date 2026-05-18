package com.watermarking.application.admin;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public class AdminCreateUserRequest {

    @NotBlank
    @Size(max = 64)
    private String username;

    @NotBlank
    @Email
    @Size(max = 64)
    private String email;

    @NotBlank
    @Size(min = 6, max = 128)
    private String password;

    /** 默认 member */
    private String role = "member";

    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public String getRole() {
        return role;
    }

    public void setRole(String role) {
        this.role = role;
    }
}

package com.watermarking.web.ui;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
public class AuthPageController {

    @GetMapping("/signin")
    public String signin() {
        return "signin";
    }

    @GetMapping("/register")
    public String register() {
        return "register";
    }

    @GetMapping("/signout")
    public String signout() {
        return "signout";
    }
}

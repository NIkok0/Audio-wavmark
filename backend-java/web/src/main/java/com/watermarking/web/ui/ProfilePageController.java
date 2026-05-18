package com.watermarking.web.ui;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
public class ProfilePageController {

    @GetMapping("/profile/retention")
    public String retention() {
        return "profile/retention";
    }
}

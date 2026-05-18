package com.watermarking.web.ui;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
public class AdminPageController {

    @GetMapping({"/admin/permission", "/admin/permission_management"})
    public String permission() {
        return "admin/permission_management";
    }
}

package com.watermarking.web.ui;

import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ModelAttribute;

@ControllerAdvice(basePackages = "com.watermarking.web.ui")
public class GlobalUiModelAdvice {

    @ModelAttribute
    public void defaultNavMedia(Model model) {
        if (!model.containsAttribute("activeMedia")) {
            model.addAttribute("activeMedia", "");
        }
    }
}

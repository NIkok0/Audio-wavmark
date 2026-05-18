package com.watermarking.web.ui;

import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@Controller
public class FilePageController {

    private final MediaUiModelHelper mediaUiModelHelper;

    public FilePageController(MediaUiModelHelper mediaUiModelHelper) {
        this.mediaUiModelHelper = mediaUiModelHelper;
    }

    @GetMapping("/{media:(?:image|audio|video|text)}/upload")
    public String upload(@PathVariable String media, Model model) {
        return workflow(media, model, "upload", "上传");
    }

    @GetMapping("/{media:(?:image|audio|video|text)}/add")
    public String add(@PathVariable String media, Model model) {
        return workflow(media, model, "add", "嵌入水印");
    }

    @GetMapping("/{media:(?:image|audio|video|text)}/extract")
    public String extract(@PathVariable String media, Model model) {
        return workflow(media, model, "extract", "提取水印");
    }

    @GetMapping("/{media:(?:image|audio|video|text)}/process")
    public String process(@PathVariable String media, Model model) {
        return workflow(media, model, "process", "处理流程");
    }

    private String workflow(String media, Model model, String stepKey, String stepTitle) {
        String m = mediaUiModelHelper.normalizedMedia(media);
        mediaUiModelHelper.validateMedia(m);
        mediaUiModelHelper.addMediaNav(model, m);
        model.addAttribute("stepKey", stepKey);
        model.addAttribute("stepTitle", stepTitle);
        return "media/workflow";
    }
}

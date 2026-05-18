package com.watermarking.web.ui;

import org.springframework.stereotype.Component;
import org.springframework.ui.Model;

import java.util.Locale;
import java.util.Map;
import java.util.Set;

@Component
public class MediaUiModelHelper {

    private static final Set<String> MEDIA = Set.of("image", "audio", "video", "text");

    private static final Map<String, String> LABELS =
            Map.of("image", "图片", "audio", "音频", "video", "视频", "text", "文档");

    public void addMediaNav(Model model, String media) {
        if (!MEDIA.contains(media)) {
            throw new IllegalArgumentException("Unsupported media: " + media);
        }
        model.addAttribute("media", media);
        model.addAttribute("mediaLabel", LABELS.getOrDefault(media, media));
        model.addAttribute("processUrl", "/" + media + "/process");
        model.addAttribute("uploadUrl", "/" + media + "/upload");
        model.addAttribute("addUrl", "/" + media + "/add");
        model.addAttribute("extractUrl", "/" + media + "/extract");
        model.addAttribute("activeMedia", media);
    }

    public void validateMedia(String media) {
        if (!MEDIA.contains(media.toLowerCase(Locale.ROOT))) {
            throw new IllegalArgumentException("Unsupported media: " + media);
        }
    }

    public String normalizedMedia(String media) {
        return media.toLowerCase(Locale.ROOT);
    }
}

package com.watermarking.web.api.files;

import com.watermarking.application.auth.DomainUserDetails;
import com.watermarking.application.files.CompleteUploadCommand;
import com.watermarking.application.files.FileResponse;
import com.watermarking.application.files.FileService;
import com.watermarking.application.files.PagedFilesResponse;
import com.watermarking.domain.model.User;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.core.io.Resource;
import org.springframework.http.ContentDisposition;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import jakarta.validation.Valid;
import java.io.IOException;
import java.net.URI;
import java.nio.charset.StandardCharsets;

/**
 * 阶段 2：文件元数据 + 本机存储；对齐 Flask {@code /download/&lt;id&gt;} 等为 REST。
 */
@RestController
@RequestMapping("/api/v1/files")
@Tag(name = "Files", description = "文件上传（本机 multipart / 对象存储 complete）、分页、详情、删除与下载")
public class FilesController {

    private final FileService fileService;

    public FilesController(FileService fileService) {
        this.fileService = fileService;
    }

    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @Operation(
            summary = "上传文件",
            description =
                    "multipart 字段：`file`（二进制）、`mediaType`（image|audio|video|text）。"
                            + "落盘路径语义与 Flask `INSTANCE_PATH` + `MEDIA_FOLDERS` + `path_utils` 一致。"
                            + "COS 直传前的过渡方案。")
    public ResponseEntity<FileResponse> upload(
            @RequestParam("mediaType") String mediaType, @RequestPart("file") MultipartFile file) throws IOException {
        if (file == null || file.isEmpty()) {
            throw new IllegalArgumentException("没有选择文件");
        }
        User user = currentUser();
        FileResponse body =
                fileService.upload(
                        user.getId(),
                        user.getUsername(),
                        mediaType,
                        file.getOriginalFilename(),
                        file.getInputStream(),
                        file.getSize());
        return ResponseEntity.status(HttpStatus.CREATED).body(body);
    }

    @PostMapping("/complete")
    @Operation(
            summary = "对象存储直传完成登记",
            description =
                    "客户端经 `POST /api/v1/storage/sts` 拿到凭证或预签名 URL 上传完成后调用；"
                            + "服务端 Head 校验 ETag 与 size，计算 SHA256 后写入 `files` 表，`original_path` 为 `s3://bucket/key`。")
    public ResponseEntity<FileResponse> completeObjectUpload(@Valid @RequestBody CompleteUploadCommand body) throws IOException {
        User user = currentUser();
        FileResponse saved = fileService.completeObjectUpload(user.getId(), body);
        return ResponseEntity.status(HttpStatus.CREATED).body(saved);
    }

    @GetMapping
    @Operation(
            summary = "分页列出当前用户文件",
            description = "可选 `fileType` 过滤；`q` 为文件名模糊搜索（仅本人）；`page` 从 0 开始。")
    public PagedFilesResponse list(
            @RequestParam(required = false) String fileType,
            @RequestParam(required = false) String q,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        User user = currentUser();
        return fileService.listForUploader(user.getId(), fileType, q, page, size);
    }

    @GetMapping("/{id}")
    @Operation(summary = "文件详情")
    public FileResponse get(@PathVariable("id") int id) {
        User user = currentUser();
        return fileService.getForUploader(user.getId(), id);
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除文件", description = "与 Flask `delete_file` 一致：已加水印仅删 watermarked_path，否则删 original_path。")
    public ResponseEntity<Void> delete(@PathVariable("id") int id) throws IOException {
        User user = currentUser();
        fileService.deleteForUploader(user.getId(), id);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/{id}/content")
    @Operation(
            summary = "下载文件内容",
            description =
                    "对齐 Flask `/download/<id>`：优先已加水印文件，否则原始文件；以附件形式返回二进制。"
                            + "对象存储路径返回 **302** 至短期预签名 GET；本机路径仍直接流式下载。")
    public ResponseEntity<?> downloadContent(@PathVariable("id") int id) throws IOException {
        User user = currentUser();
        FileService.LoadedContent loaded = fileService.loadContentForUploader(user.getId(), id);
        if (loaded.redirect()) {
            return ResponseEntity.status(HttpStatus.FOUND).location(URI.create(loaded.redirectUrl())).build();
        }
        ContentDisposition disposition =
                ContentDisposition.attachment().filename(loaded.downloadFilename(), StandardCharsets.UTF_8).build();
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, disposition.toString())
                .contentType(MediaType.parseMediaType(loaded.mimeType()))
                .body(loaded.resource());
    }

    private static User currentUser() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || !(auth.getPrincipal() instanceof DomainUserDetails details)) {
            throw new AccessDeniedException("需要登录");
        }
        return details.getUser();
    }
}

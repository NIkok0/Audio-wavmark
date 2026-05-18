package com.watermarking.application.files;

import java.util.List;

public record PagedFilesResponse(List<FileResponse> content, long totalElements, int page, int size) {}

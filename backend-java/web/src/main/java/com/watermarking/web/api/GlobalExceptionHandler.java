package com.watermarking.web.api;

import com.watermarking.application.auth.RegistrationConflictException;
import com.watermarking.application.files.FileAccessDeniedException;
import com.watermarking.infrastructure.storage.ObjectStorageUnavailableException;
import com.watermarking.application.files.InvalidFileUploadException;
import com.watermarking.application.admin.AdminAccessDeniedException;
import com.watermarking.application.admin.AdminUserNotFoundException;
import com.watermarking.application.files.StoredFileNotFoundException;
import com.watermarking.application.jobs.InvalidWatermarkJobStateException;
import com.watermarking.application.jobs.WatermarkJobEnqueueException;
import com.watermarking.application.jobs.WatermarkJobNotFoundException;
import com.watermarking.web.api.auth.AccountInactiveException;
import com.watermarking.web.api.auth.FlaskStyleBadCredentialsException;
import com.watermarking.web.api.auth.LoginFieldsRequiredException;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.io.IOException;
import java.net.URI;

@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final URI TYPE_VALIDATION = URI.create("urn:watermarking:validation");
    private static final URI TYPE_CONFLICT = URI.create("urn:watermarking:conflict");
    private static final URI TYPE_AUTH = URI.create("urn:watermarking:authentication");
    private static final URI TYPE_STORAGE = URI.create("urn:watermarking:storage");
    private static final URI TYPE_JOBS = URI.create("urn:watermarking:jobs");
    private static final URI TYPE_ADMIN = URI.create("urn:watermarking:admin");

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ProblemDetail> handleValidation(MethodArgumentNotValidException ex, HttpServletRequest request) {
        ProblemDetail pd = ProblemDetail.forStatus(HttpStatus.BAD_REQUEST);
        pd.setTitle("Validation failed");
        pd.setType(TYPE_VALIDATION);
        pd.setInstance(URI.create(request.getRequestURI()));
        StringBuilder detail = new StringBuilder();
        ex.getBindingResult().getFieldErrors().forEach(fe -> {
            if (!detail.isEmpty()) {
                detail.append("; ");
            }
            detail.append(fe.getField()).append(": ").append(fe.getDefaultMessage());
        });
        pd.setDetail(detail.toString());
        return ResponseEntity.badRequest().body(pd);
    }

    @ExceptionHandler(RegistrationConflictException.class)
    public ResponseEntity<ProblemDetail> handleConflict(RegistrationConflictException ex, HttpServletRequest request) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(HttpStatus.CONFLICT, ex.getMessage());
        pd.setTitle("Registration conflict");
        pd.setType(TYPE_CONFLICT);
        pd.setInstance(URI.create(request.getRequestURI()));
        pd.setProperty("field", ex.getField().name());
        return ResponseEntity.status(HttpStatus.CONFLICT).body(pd);
    }

    @ExceptionHandler(LoginFieldsRequiredException.class)
    public ResponseEntity<ProblemDetail> handleLoginFields(LoginFieldsRequiredException ex, HttpServletRequest request) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST, ex.getMessage());
        pd.setTitle("Login validation");
        pd.setType(TYPE_VALIDATION);
        pd.setInstance(URI.create(request.getRequestURI()));
        return ResponseEntity.badRequest().body(pd);
    }

    @ExceptionHandler(FlaskStyleBadCredentialsException.class)
    public ResponseEntity<ProblemDetail> handleBadCredentials(FlaskStyleBadCredentialsException ex, HttpServletRequest request) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(HttpStatus.UNAUTHORIZED, ex.getMessage());
        pd.setTitle("Unauthorized");
        pd.setType(TYPE_AUTH);
        pd.setInstance(URI.create(request.getRequestURI()));
        return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(pd);
    }

    @ExceptionHandler(AccountInactiveException.class)
    public ResponseEntity<ProblemDetail> handleInactive(AccountInactiveException ex, HttpServletRequest request) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(HttpStatus.FORBIDDEN, ex.getMessage());
        pd.setTitle("Forbidden");
        pd.setType(TYPE_AUTH);
        pd.setInstance(URI.create(request.getRequestURI()));
        return ResponseEntity.status(HttpStatus.FORBIDDEN).body(pd);
    }

    @ExceptionHandler(InvalidFileUploadException.class)
    public ResponseEntity<ProblemDetail> handleInvalidUpload(InvalidFileUploadException ex, HttpServletRequest request) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST, ex.getMessage());
        pd.setTitle("Invalid upload");
        pd.setType(TYPE_VALIDATION);
        pd.setInstance(URI.create(request.getRequestURI()));
        return ResponseEntity.badRequest().body(pd);
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<ProblemDetail> handleIllegalArgument(IllegalArgumentException ex, HttpServletRequest request) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST, ex.getMessage());
        pd.setTitle("Bad request");
        pd.setType(TYPE_VALIDATION);
        pd.setInstance(URI.create(request.getRequestURI()));
        return ResponseEntity.badRequest().body(pd);
    }

    @ExceptionHandler(StoredFileNotFoundException.class)
    public ResponseEntity<ProblemDetail> handleFileNotFound(StoredFileNotFoundException ex, HttpServletRequest request) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
        pd.setTitle("Not found");
        pd.setType(TYPE_STORAGE);
        pd.setInstance(URI.create(request.getRequestURI()));
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(pd);
    }

    @ExceptionHandler(FileAccessDeniedException.class)
    public ResponseEntity<ProblemDetail> handleFileAccessDenied(FileAccessDeniedException ex, HttpServletRequest request) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(HttpStatus.FORBIDDEN, ex.getMessage());
        pd.setTitle("Forbidden");
        pd.setType(TYPE_STORAGE);
        pd.setInstance(URI.create(request.getRequestURI()));
        return ResponseEntity.status(HttpStatus.FORBIDDEN).body(pd);
    }

    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<ProblemDetail> handleAccessDenied(AccessDeniedException ex, HttpServletRequest request) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(HttpStatus.FORBIDDEN, ex.getMessage());
        pd.setTitle("Forbidden");
        pd.setType(TYPE_AUTH);
        pd.setInstance(URI.create(request.getRequestURI()));
        return ResponseEntity.status(HttpStatus.FORBIDDEN).body(pd);
    }

    @ExceptionHandler(IOException.class)
    public ResponseEntity<ProblemDetail> handleIOException(IOException ex, HttpServletRequest request) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(HttpStatus.INTERNAL_SERVER_ERROR, "存储读写失败");
        pd.setTitle("Storage error");
        pd.setType(TYPE_STORAGE);
        pd.setInstance(URI.create(request.getRequestURI()));
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(pd);
    }

    @ExceptionHandler(SecurityException.class)
    public ResponseEntity<ProblemDetail> handleSecurityException(SecurityException ex, HttpServletRequest request) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(HttpStatus.FORBIDDEN, "拒绝访问");
        pd.setTitle("Forbidden");
        pd.setType(TYPE_STORAGE);
        pd.setInstance(URI.create(request.getRequestURI()));
        return ResponseEntity.status(HttpStatus.FORBIDDEN).body(pd);
    }

    @ExceptionHandler(ObjectStorageUnavailableException.class)
    public ResponseEntity<ProblemDetail> handleObjectStorageUnavailable(
            ObjectStorageUnavailableException ex, HttpServletRequest request) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(HttpStatus.SERVICE_UNAVAILABLE, ex.getMessage());
        pd.setTitle("Object storage unavailable");
        pd.setType(TYPE_STORAGE);
        pd.setInstance(URI.create(request.getRequestURI()));
        return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(pd);
    }

    @ExceptionHandler(WatermarkJobNotFoundException.class)
    public ResponseEntity<ProblemDetail> handleJobNotFound(WatermarkJobNotFoundException ex, HttpServletRequest request) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
        pd.setTitle("Job not found");
        pd.setType(TYPE_JOBS);
        pd.setInstance(URI.create(request.getRequestURI()));
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(pd);
    }

    @ExceptionHandler(InvalidWatermarkJobStateException.class)
    public ResponseEntity<ProblemDetail> handleInvalidJobState(InvalidWatermarkJobStateException ex, HttpServletRequest request) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(HttpStatus.CONFLICT, ex.getMessage());
        pd.setTitle("Invalid job state");
        pd.setType(TYPE_JOBS);
        pd.setInstance(URI.create(request.getRequestURI()));
        return ResponseEntity.status(HttpStatus.CONFLICT).body(pd);
    }

    @ExceptionHandler(WatermarkJobEnqueueException.class)
    public ResponseEntity<ProblemDetail> handleJobEnqueue(WatermarkJobEnqueueException ex, HttpServletRequest request) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(HttpStatus.SERVICE_UNAVAILABLE, ex.getMessage());
        pd.setTitle("Job enqueue failed");
        pd.setType(TYPE_JOBS);
        pd.setInstance(URI.create(request.getRequestURI()));
        return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(pd);
    }

    @ExceptionHandler(AdminAccessDeniedException.class)
    public ResponseEntity<ProblemDetail> handleAdminAccess(AdminAccessDeniedException ex, HttpServletRequest request) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(HttpStatus.FORBIDDEN, ex.getMessage());
        pd.setTitle("Forbidden");
        pd.setType(TYPE_ADMIN);
        pd.setInstance(URI.create(request.getRequestURI()));
        return ResponseEntity.status(HttpStatus.FORBIDDEN).body(pd);
    }

    @ExceptionHandler(AdminUserNotFoundException.class)
    public ResponseEntity<ProblemDetail> handleAdminUserNotFound(AdminUserNotFoundException ex, HttpServletRequest request) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
        pd.setTitle("Not found");
        pd.setType(TYPE_ADMIN);
        pd.setInstance(URI.create(request.getRequestURI()));
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(pd);
    }
}

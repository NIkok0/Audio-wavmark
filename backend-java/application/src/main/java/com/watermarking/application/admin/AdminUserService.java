package com.watermarking.application.admin;

import com.watermarking.application.auth.RegistrationConflictException;
import com.watermarking.application.auth.RegistrationConflictException.ConflictField;
import com.watermarking.domain.model.Group;
import com.watermarking.domain.model.User;
import com.watermarking.infrastructure.persistence.FileRepository;
import com.watermarking.infrastructure.persistence.UserRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Locale;
import java.util.Set;
import java.util.stream.Collectors;

@Service
public class AdminUserService {

    private final UserRepository userRepository;
    private final FileRepository fileRepository;
    private final PasswordEncoder passwordEncoder;

    public AdminUserService(UserRepository userRepository, FileRepository fileRepository, PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.fileRepository = fileRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Transactional(readOnly = true)
    public PagedAdminUsersResponse list(User viewer, String search, String roleFilter, Boolean active, int page, int size) {
        requireManageGroups(viewer);
        User v = userRepository.findWithGroupsById(viewer.getId()).orElse(viewer);
        Specification<User> spec = AdminUserSpecifications.viewerScope(v);
        spec = spec.and(AdminUserSpecifications.search(search));
        spec = spec.and(AdminUserSpecifications.roleEquals(roleFilter));
        spec = spec.and(AdminUserSpecifications.activeFilter(active));

        int p = Math.max(0, page);
        int s = Math.min(100, Math.max(1, size));
        PageRequest pr = PageRequest.of(p, s, Sort.by(Sort.Direction.DESC, "createdAt"));
        Page<User> result = userRepository.findAll(spec, pr);
        return new PagedAdminUsersResponse(
                result.getContent().stream().map(AdminUserResponse::fromEntity).toList(),
                result.getTotalElements(),
                result.getNumber(),
                result.getSize());
    }

    @Transactional(readOnly = true)
    public AdminUserResponse get(User viewer, int targetId) {
        requireManageGroups(viewer);
        User v = userRepository.findWithGroupsById(viewer.getId()).orElse(viewer);
        User t =
                userRepository
                        .findWithGroupsById(targetId)
                        .orElseThrow(() -> new AdminUserNotFoundException("用户不存在"));
        assertCanAccessTarget(v, t);
        return AdminUserResponse.fromEntity(t);
    }

    @Transactional
    public AdminUserResponse patch(User viewer, int targetId, AdminPatchUserRequest body) {
        requireManageGroups(viewer);
        User v = userRepository.findWithGroupsById(viewer.getId()).orElse(viewer);
        User t =
                userRepository
                        .findWithGroupsById(targetId)
                        .orElseThrow(() -> new AdminUserNotFoundException("用户不存在"));
        assertCanManageTargetForMutation(v, t);

        if (body.getUsername() != null && !body.getUsername().isBlank()) {
            String nu = body.getUsername().trim();
            if (!nu.equals(t.getUsername())
                    && userRepository.findByUsername(nu).isPresent()) {
                throw new RegistrationConflictException(ConflictField.USERNAME, "用户名已存在");
            }
            t.setUsername(nu);
        }
        if (body.getEmail() != null && !body.getEmail().isBlank()) {
            String ne = body.getEmail().trim();
            if (!ne.equalsIgnoreCase(t.getEmail())
                    && userRepository.findByEmail(ne).isPresent()) {
                throw new RegistrationConflictException(ConflictField.EMAIL, "邮箱已被注册");
            }
            t.setEmail(ne);
        }
        if (body.getRole() != null && !body.getRole().isBlank()) {
            if ("super_admin".equalsIgnoreCase(body.getRole().trim()) && !v.isSuperAdmin()) {
                throw new AdminAccessDeniedException("无权设置超级管理员角色");
            }
            applyRole(t, body.getRole().trim());
        }
        if (body.getActive() != null) {
            t.setActive(body.getActive());
        }
        if (body.getEmbed() != null) {
            t.setEmbed(body.getEmbed());
        }
        if (body.getExtract() != null) {
            t.setExtract(body.getExtract());
        }
        if (body.getRetentionDays() != null) {
            t.setRetentionDays(body.getRetentionDays());
        }

        return AdminUserResponse.fromEntity(userRepository.save(t));
    }

    @Transactional
    public AdminUserResponse create(User viewer, AdminCreateUserRequest body) {
        requireManageGroups(viewer);
        User v = userRepository.findWithGroupsById(viewer.getId()).orElse(viewer);
        String role = body.getRole() == null ? "member" : body.getRole().trim();
        if ("super_admin".equalsIgnoreCase(role) && !v.isSuperAdmin()) {
            throw new AdminAccessDeniedException("无权创建超级管理员");
        }
        if (userRepository.findByUsername(body.getUsername().trim()).isPresent()) {
            throw new RegistrationConflictException(ConflictField.USERNAME, "用户名已存在");
        }
        if (userRepository.findByEmail(body.getEmail().trim()).isPresent()) {
            throw new RegistrationConflictException(ConflictField.EMAIL, "邮箱已被注册");
        }

        User u = new User();
        u.setUsername(body.getUsername().trim());
        u.setEmail(body.getEmail().trim());
        u.setPassword(passwordEncoder.encode(body.getPassword()));
        applyRole(u, role);
        u.setActive(true);
        u.setEmbed(true);
        u.setExtract(true);
        User saved = userRepository.save(u);
        return AdminUserResponse.fromEntity(userRepository.findWithGroupsById(saved.getId()).orElse(saved));
    }

    @Transactional
    public void delete(User viewer, int targetId) {
        User v = userRepository.findWithGroupsById(viewer.getId()).orElse(viewer);
        requireSuperAdmin(v);
        if (v.getId().equals(targetId)) {
            throw new AdminAccessDeniedException("不能删除当前登录用户");
        }
        User target = userRepository
                .findWithGroupsById(targetId)
                .orElseThrow(() -> new AdminUserNotFoundException("用户不存在"));
        fileRepository.findByUploader_IdOrderByCreatedAtDesc(target.getId(), org.springframework.data.domain.Pageable.unpaged())
                .forEach(fileRepository::delete);
        userRepository.delete(target);
    }

    @Transactional
    public void batchDelete(User viewer, java.util.List<Integer> targetIds) {
        User v = userRepository.findWithGroupsById(viewer.getId()).orElse(viewer);
        requireSuperAdmin(v);
        if (targetIds == null || targetIds.isEmpty()) {
            throw new IllegalArgumentException("请选择要删除的用户");
        }
        for (Integer id : targetIds.stream().filter(java.util.Objects::nonNull).distinct().toList()) {
            delete(v, id);
        }
    }

    private static void requireManageGroups(User viewer) {
        if (!viewer.canManageGroups()) {
            throw new AdminAccessDeniedException("需要管理员权限");
        }
    }

    private static void requireSuperAdmin(User viewer) {
        if (!viewer.isSuperAdmin()) {
            throw new AdminAccessDeniedException("需要超级管理员权限");
        }
    }

    private static void assertCanAccessTarget(User viewer, User target) {
        if (viewer.isSuperAdmin()) {
            return;
        }
        if (viewer.getId().equals(target.getId())) {
            return;
        }
        if (target.isSuperAdmin()) {
            throw new AdminAccessDeniedException("无权查看该用户");
        }
        Set<Integer> vg = viewer.getGroups().stream().map(Group::getId).collect(Collectors.toSet());
        boolean share = target.getGroups().stream().anyMatch(g -> vg.contains(g.getId()));
        if (!share) {
            throw new AdminAccessDeniedException("无权查看该用户");
        }
    }

    private static void assertCanManageTargetForMutation(User viewer, User target) {
        if (viewer.getId().equals(target.getId())) {
            throw new AdminAccessDeniedException("不能通过管理接口编辑自己的账号");
        }
        assertCanAccessTarget(viewer, target);
    }

    private static void applyRole(User u, String roleRaw) {
        String r = roleRaw.toLowerCase(Locale.ROOT);
        if (!Set.of("member", "admin", "super_admin").contains(r)) {
            throw new IllegalArgumentException("非法角色: " + roleRaw);
        }
        u.setRole(r);
        u.setAdmin("admin".equals(r) || "super_admin".equals(r));
    }
}

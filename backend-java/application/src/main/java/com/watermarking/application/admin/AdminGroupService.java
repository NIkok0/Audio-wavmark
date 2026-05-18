package com.watermarking.application.admin;

import com.watermarking.domain.model.Group;
import com.watermarking.domain.model.File;
import com.watermarking.domain.model.User;
import com.watermarking.infrastructure.persistence.GroupRepository;
import com.watermarking.infrastructure.persistence.UserRepository;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Comparator;
import java.util.List;

@Service
public class AdminGroupService {

    private final UserRepository userRepository;
    private final GroupRepository groupRepository;

    public AdminGroupService(UserRepository userRepository, GroupRepository groupRepository) {
        this.userRepository = userRepository;
        this.groupRepository = groupRepository;
    }

    @Transactional(readOnly = true)
    public List<AdminGroupResponse> list(User viewer) {
        if (!viewer.canManageGroups()) {
            throw new AdminAccessDeniedException("需要管理员权限");
        }
        User v = userRepository.findWithGroupsById(viewer.getId()).orElse(viewer);
        if (v.isSuperAdmin()) {
            return groupRepository.findAll(Sort.by("name")).stream().map(AdminGroupResponse::fromEntity).toList();
        }
        return v.getGroups().stream()
                .sorted(Comparator.comparing(Group::getName, String.CASE_INSENSITIVE_ORDER))
                .map(AdminGroupResponse::fromEntity)
                .toList();
    }

    @Transactional
    public AdminGroupResponse create(User viewer, AdminGroupRequest body) {
        requireSuperAdmin(viewer);
        String name = cleanName(body.getName());
        if (groupRepository.findByName(name).isPresent()) {
            throw new IllegalArgumentException("组名已存在");
        }
        Group g = new Group();
        g.setName(name);
        g.setDescription(cleanDescription(body.getDescription()));
        return AdminGroupResponse.fromEntity(groupRepository.save(g));
    }

    @Transactional
    public AdminGroupResponse patch(User viewer, int groupId, AdminGroupRequest body) {
        requireSuperAdmin(viewer);
        Group g = groupRepository.findById(groupId).orElseThrow(() -> new IllegalArgumentException("组不存在"));
        String name = cleanName(body.getName());
        groupRepository.findByName(name).ifPresent(existing -> {
            if (!existing.getId().equals(groupId)) {
                throw new IllegalArgumentException("组名已存在");
            }
        });
        g.setName(name);
        g.setDescription(cleanDescription(body.getDescription()));
        return AdminGroupResponse.fromEntity(groupRepository.save(g));
    }

    @Transactional
    public void delete(User viewer, int groupId) {
        requireSuperAdmin(viewer);
        Group g = groupRepository.findById(groupId).orElseThrow(() -> new IllegalArgumentException("组不存在"));
        for (User u : List.copyOf(g.getUsers())) {
            u.getGroups().remove(g);
        }
        for (File f : List.copyOf(g.getFiles())) {
            f.setGroup(null);
        }
        groupRepository.delete(g);
    }

    private static void requireSuperAdmin(User viewer) {
        if (!viewer.isSuperAdmin()) {
            throw new AdminAccessDeniedException("需要超级管理员权限");
        }
    }

    private static String cleanName(String raw) {
        if (raw == null || raw.isBlank()) {
            throw new IllegalArgumentException("组名不能为空");
        }
        return raw.trim();
    }

    private static String cleanDescription(String raw) {
        return raw == null ? "" : raw.trim();
    }
}

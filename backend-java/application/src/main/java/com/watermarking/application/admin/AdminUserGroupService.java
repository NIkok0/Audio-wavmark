package com.watermarking.application.admin;

import com.watermarking.domain.model.Group;
import com.watermarking.domain.model.User;
import com.watermarking.infrastructure.persistence.GroupRepository;
import com.watermarking.infrastructure.persistence.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.stream.Collectors;

@Service
public class AdminUserGroupService {

    private final UserRepository userRepository;
    private final GroupRepository groupRepository;

    public AdminUserGroupService(UserRepository userRepository, GroupRepository groupRepository) {
        this.userRepository = userRepository;
        this.groupRepository = groupRepository;
    }

    @Transactional
    public AdminUserResponse addUserToGroup(User viewer, int userId, int groupId) {
        if (!viewer.canManageGroups()) {
            throw new AdminAccessDeniedException("需要管理员权限");
        }
        User v = userRepository.findWithGroupsById(viewer.getId()).orElse(viewer);
        User t = userRepository
                .findWithGroupsById(userId)
                .orElseThrow(() -> new AdminUserNotFoundException("用户不存在"));
        Group g = groupRepository.findById(groupId).orElseThrow(() -> new IllegalArgumentException("组不存在"));

        assertCanAccessUserGroups(v, t);
        assertAdminMayUseGroup(v, groupId);

        t.getGroups().add(g);
        return AdminUserResponse.fromEntity(userRepository.save(t));
    }

    @Transactional
    public AdminUserResponse removeUserFromGroup(User viewer, int userId, int groupId) {
        if (!viewer.canManageGroups()) {
            throw new AdminAccessDeniedException("需要管理员权限");
        }
        User v = userRepository.findWithGroupsById(viewer.getId()).orElse(viewer);
        User t = userRepository
                .findWithGroupsById(userId)
                .orElseThrow(() -> new AdminUserNotFoundException("用户不存在"));

        assertCanAccessUserGroups(v, t);
        assertAdminMayUseGroup(v, groupId);

        t.getGroups().removeIf(x -> x.getId().equals(groupId));
        return AdminUserResponse.fromEntity(userRepository.save(t));
    }

    private static void assertCanAccessUserGroups(User viewer, User target) {
        if (viewer.isSuperAdmin()) {
            return;
        }
        if (viewer.getId().equals(target.getId())) {
            return;
        }
        if (target.isSuperAdmin()) {
            throw new AdminAccessDeniedException("无权操作该用户");
        }
        var vg = viewer.getGroups().stream().map(Group::getId).collect(Collectors.toSet());
        boolean share = target.getGroups().stream().anyMatch(g -> vg.contains(g.getId()));
        if (!share) {
            throw new AdminAccessDeniedException("无权操作该用户");
        }
    }

    private static void assertAdminMayUseGroup(User viewer, int groupId) {
        if (viewer.isSuperAdmin()) {
            return;
        }
        boolean ok = viewer.getGroups().stream().anyMatch(g -> g.getId().equals(groupId));
        if (!ok) {
            throw new AdminAccessDeniedException("无权操作该组");
        }
    }
}

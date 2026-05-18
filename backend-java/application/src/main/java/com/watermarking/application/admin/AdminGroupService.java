package com.watermarking.application.admin;

import com.watermarking.domain.model.Group;
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
}

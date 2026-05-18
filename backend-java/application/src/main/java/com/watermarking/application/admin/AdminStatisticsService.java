package com.watermarking.application.admin;

import com.watermarking.domain.model.User;
import com.watermarking.infrastructure.persistence.GroupRepository;
import com.watermarking.infrastructure.persistence.UserRepository;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AdminStatisticsService {

    private final UserRepository userRepository;
    private final GroupRepository groupRepository;

    public AdminStatisticsService(UserRepository userRepository, GroupRepository groupRepository) {
        this.userRepository = userRepository;
        this.groupRepository = groupRepository;
    }

    @Transactional(readOnly = true)
    public AdminStatsResponse stats(User viewer) {
        if (!viewer.canManageGroups()) {
            throw new AdminAccessDeniedException("需要管理员权限");
        }
        User v = userRepository.findWithGroupsById(viewer.getId()).orElse(viewer);

        Specification<User> scope = AdminUserSpecifications.viewerScope(v);
        long totalUsers = userRepository.count(scope);
        long activeUsers = userRepository.count(scope.and(AdminUserSpecifications.activeFilter(true)));
        long adminUsers = userRepository.count(scope.and(AdminUserSpecifications.roleAdminOrSuperAdmin()));

        long totalGroups;
        if (v.isSuperAdmin()) {
            totalGroups = groupRepository.count();
        } else {
            totalGroups = v.getGroups().size();
        }

        return new AdminStatsResponse(totalUsers, activeUsers, adminUsers, totalGroups);
    }
}

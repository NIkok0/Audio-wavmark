package com.watermarking.application.admin;

import com.watermarking.domain.model.Group;
import com.watermarking.domain.model.User;
import org.springframework.data.jpa.domain.Specification;

import jakarta.persistence.criteria.JoinType;
import java.util.Collection;
import java.util.Set;
import java.util.stream.Collectors;

public final class AdminUserSpecifications {

    private AdminUserSpecifications() {}

    /** 与 {@link AdminUserService} 列表范围一致：超管全库，普通管理员仅同组用户（无组时仅本人） */
    public static Specification<User> viewerScope(User viewer) {
        if (viewer.isSuperAdmin()) {
            return (root, query, cb) -> cb.conjunction();
        }
        Set<Integer> gids = viewer.getGroups().stream().map(Group::getId).collect(Collectors.toSet());
        if (gids.isEmpty()) {
            return idEquals(viewer.getId());
        }
        return inAnyGroup(gids);
    }

    public static Specification<User> roleAdminOrSuperAdmin() {
        return (root, query, cb) -> root.get("role").in("admin", "super_admin");
    }

    public static Specification<User> search(String q) {
        if (q == null || q.isBlank()) {
            return (root, query, cb) -> cb.conjunction();
        }
        String p = "%" + q.trim().toLowerCase() + "%";
        return (root, query, cb) ->
                cb.or(cb.like(cb.lower(root.get("username")), p), cb.like(cb.lower(root.get("email")), p));
    }

    public static Specification<User> roleEquals(String role) {
        if (role == null || role.isBlank()) {
            return (root, query, cb) -> cb.conjunction();
        }
        return (root, query, cb) -> cb.equal(root.get("role"), role.trim());
    }

    public static Specification<User> activeFilter(Boolean active) {
        if (active == null) {
            return (root, query, cb) -> cb.conjunction();
        }
        return (root, query, cb) -> cb.equal(root.get("active"), active);
    }

    public static Specification<User> inAnyGroup(Collection<Integer> groupIds) {
        return (root, query, cb) -> {
            query.distinct(true);
            var j = root.join("groups", JoinType.INNER);
            return j.get("id").in(groupIds);
        };
    }

    public static Specification<User> idEquals(int id) {
        return (root, query, cb) -> cb.equal(root.get("id"), id);
    }
}

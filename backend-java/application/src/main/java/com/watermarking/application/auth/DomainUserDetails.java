package com.watermarking.application.auth;

import com.watermarking.domain.model.User;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

/**
 * Spring Session（Redis）会序列化 SecurityContext；不可直接持有带 JPA 关联的 {@link User}。
 */
public class DomainUserDetails implements UserDetails, Serializable {

    private static final long serialVersionUID = 1L;

    private final User user;

    public DomainUserDetails(User user) {
        this.user = snapshot(user);
    }

    /** 仅保留会话所需标量字段，避免 Redis 序列化失败。 */
    private static User snapshot(User source) {
        User u = new User();
        u.setId(source.getId());
        u.setUsername(source.getUsername());
        u.setEmail(source.getEmail());
        u.setPassword(source.getPassword());
        u.setAdmin(source.isAdmin());
        u.setRole(source.getRole());
        u.setActive(source.isActive());
        u.setEmbed(source.isEmbed());
        u.setExtract(source.isExtract());
        u.setRetentionDays(source.getRetentionDays());
        u.setCreatedAt(source.getCreatedAt());
        u.setUpdatedAt(source.getUpdatedAt());
        return u;
    }

    public User getUser() {
        return user;
    }

    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        List<GrantedAuthority> authorities = new ArrayList<>();
        authorities.add(new SimpleGrantedAuthority("ROLE_USER"));
        if (user.isAdminUser()) {
            authorities.add(new SimpleGrantedAuthority("ROLE_ADMIN"));
        }
        if (user.isSuperAdmin()) {
            authorities.add(new SimpleGrantedAuthority("ROLE_SUPER_ADMIN"));
        }
        return authorities;
    }

    @Override
    public String getPassword() {
        return user.getPassword();
    }

    @Override
    public String getUsername() {
        return user.getUsername();
    }

    @Override
    public boolean isAccountNonExpired() {
        return true;
    }

    @Override
    public boolean isAccountNonLocked() {
        return user.isActive();
    }

    @Override
    public boolean isCredentialsNonExpired() {
        return true;
    }

    @Override
    public boolean isEnabled() {
        return user.isActive();
    }
}

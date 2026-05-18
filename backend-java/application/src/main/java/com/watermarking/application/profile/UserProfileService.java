package com.watermarking.application.profile;

import com.watermarking.domain.model.User;
import com.watermarking.infrastructure.persistence.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class UserProfileService {

    private final UserRepository userRepository;

    public UserProfileService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @Transactional
    public void updateRetentionDays(int userId, PatchRetentionRequest body) {
        User u = userRepository.findById(userId).orElseThrow();
        u.setRetentionDays(body.getRetentionDays());
        userRepository.save(u);
    }
}

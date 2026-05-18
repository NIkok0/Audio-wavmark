package com.watermarking.infrastructure.persistence;

import com.watermarking.domain.model.Group;
import org.springframework.data.jpa.repository.JpaRepository;

public interface GroupRepository extends JpaRepository<Group, Integer> {}

package com.watermarking.infrastructure.persistence;

import com.watermarking.domain.model.User;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Optional;

public interface UserRepository extends JpaRepository<User, Integer>, JpaSpecificationExecutor<User> {

    Optional<User> findByUsername(String username);

    Optional<User> findByEmail(String email);

    @Query("select u from User u where u.username = :q or u.email = :q")
    Optional<User> findByUsernameOrEmail(@Param("q") String q);

    @EntityGraph(attributePaths = {"groups"})
    @Query("select u from User u where u.id = :id")
    Optional<User> findWithGroupsById(@Param("id") Integer id);
}

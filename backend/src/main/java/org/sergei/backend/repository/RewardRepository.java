package org.sergei.backend.repository;

import org.sergei.backend.entity.Reward;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface RewardRepository extends JpaRepository<Reward, Long> {
    List<Reward> findByHouseholdIdOrderByCreatedAtDesc(Long householdId);
}

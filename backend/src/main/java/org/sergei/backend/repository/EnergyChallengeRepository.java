package org.sergei.backend.repository;

import org.sergei.backend.entity.EnergyChallenge;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface EnergyChallengeRepository extends JpaRepository<EnergyChallenge, Long> {
    List<EnergyChallenge> findByHouseholdIdOrderByCreatedAtDesc(Long householdId);
    List<EnergyChallenge> findByHouseholdIdAndStatus(Long householdId, String status);
}

package org.sergei.backend.repository;

import org.sergei.backend.entity.Insight;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface InsightRepository extends JpaRepository<Insight, Long> {
    List<Insight> findByHouseholdIdOrderByCreatedAtDesc(Long householdId);
}

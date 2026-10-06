package org.sergei.backend.repository;

import org.sergei.backend.entity.Consumption;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ConsumptionRepository extends JpaRepository<Consumption, Long> {
    List<Consumption> findByHouseholdIdOrderByBillingMonthAsc(Long householdId);
}

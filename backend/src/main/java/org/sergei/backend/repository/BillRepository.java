package org.sergei.backend.repository;

import org.sergei.backend.entity.Bill;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface BillRepository extends JpaRepository<Bill, Long> {
    List<Bill> findByHouseholdIdOrderByBillingMonthAsc(Long householdId);
}

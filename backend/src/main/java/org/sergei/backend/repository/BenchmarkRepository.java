package org.sergei.backend.repository;

import org.sergei.backend.entity.Benchmark;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface BenchmarkRepository extends JpaRepository<Benchmark, Long> {
    Optional<Benchmark> findByCityAndStateAndHouseholdSizeGroupAndHomeType(
            String city, String state, String householdSizeGroup, String homeType);
}

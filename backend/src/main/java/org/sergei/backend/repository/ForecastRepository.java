package org.sergei.backend.repository;

import org.sergei.backend.entity.Forecast;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

public interface ForecastRepository extends JpaRepository<Forecast, Long> {
    List<Forecast> findByState(String state);
    Optional<Forecast> findByStateAndForecastDate(String state, LocalDate forecastDate);
}

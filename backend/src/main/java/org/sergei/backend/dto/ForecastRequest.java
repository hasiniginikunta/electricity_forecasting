package org.sergei.backend.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.time.LocalDate;

public record ForecastRequest(
        @NotBlank String state,
        @NotNull LocalDate forecastDate,
        Double demandMw,
        Double solarCapacityFactor,
        Double windCapacityFactor,
        Double netDemandMw,
        Double renewableShare,
        String riskLevel
) {}

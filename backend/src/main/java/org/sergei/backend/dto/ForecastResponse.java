package org.sergei.backend.dto;

import org.sergei.backend.entity.Forecast;

import java.time.LocalDate;

public record ForecastResponse(Long id, String state, LocalDate forecastDate, Double demandMw,
                               Double solarCapacityFactor, Double windCapacityFactor,
                               Double netDemandMw, Double renewableShare, String riskLevel) {
    public static ForecastResponse from(Forecast f) {
        return new ForecastResponse(f.getId(), f.getState(), f.getForecastDate(), f.getDemandMw(),
                f.getSolarCapacityFactor(), f.getWindCapacityFactor(),
                f.getNetDemandMw(), f.getRenewableShare(), f.getRiskLevel());
    }
}

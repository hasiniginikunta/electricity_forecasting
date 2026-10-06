package org.sergei.backend.dto;

import org.sergei.backend.entity.Benchmark;

public record BenchmarkResponse(Long id, String city, String state, String householdSizeGroup,
                                String homeType, Double medianKwh, Double p25Kwh, Double p75Kwh, Integer sampleSize) {
    public static BenchmarkResponse from(Benchmark b) {
        return new BenchmarkResponse(b.getId(), b.getCity(), b.getState(), b.getHouseholdSizeGroup(),
                b.getHomeType(), b.getMedianKwh(), b.getP25Kwh(), b.getP75Kwh(), b.getSampleSize());
    }
}

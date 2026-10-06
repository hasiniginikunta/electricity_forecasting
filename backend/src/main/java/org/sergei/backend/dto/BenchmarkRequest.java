package org.sergei.backend.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

public record BenchmarkRequest(
        @NotBlank String city,
        @NotBlank String state,
        @NotBlank String householdSizeGroup,
        @NotBlank String homeType,
        @NotNull Double medianKwh,
        @NotNull Double p25Kwh,
        @NotNull Double p75Kwh,
        @NotNull @Positive Integer sampleSize
) {}

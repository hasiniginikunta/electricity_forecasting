package org.sergei.backend.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

public record HouseholdRequest(
        @NotNull Long userId,
        @NotNull @Positive Integer householdSize,
        @NotBlank String city,
        @NotBlank String state,
        @NotBlank String homeType
) {}

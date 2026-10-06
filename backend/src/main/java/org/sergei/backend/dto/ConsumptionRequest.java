package org.sergei.backend.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

public record ConsumptionRequest(
        @NotNull Long householdId,
        @NotBlank String billingMonth,
        @NotNull @Positive Double kwhConsumed
) {}

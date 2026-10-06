package org.sergei.backend.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

public record BillRequest(
        @NotNull Long householdId,
        @NotBlank String billingMonth,
        @NotNull @Positive Double unitsConsumed,
        @NotNull @Positive Double billAmount
) {}

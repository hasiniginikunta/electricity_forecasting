package org.sergei.backend.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

public record RewardRequest(
        @NotNull Long householdId,
        @NotNull @Positive Integer credits,
        @NotBlank String reason
) {}

package org.sergei.backend.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record InsightRequest(
        @NotNull Long householdId,
        @NotBlank String type,
        @NotBlank String message
) {}

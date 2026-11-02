package org.sergei.backend.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import java.time.LocalDate;

public record ChallengeRequest(
        @NotNull Long householdId,
        @NotBlank String title,
        @NotBlank String description,
        @NotNull @Positive Double targetKwh,
        @NotNull @Positive Integer creditReward,
        @NotNull LocalDate startDate,
        @NotNull LocalDate endDate
) {}

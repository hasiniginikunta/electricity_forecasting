package org.sergei.backend.dto;

import org.sergei.backend.entity.EnergyChallenge;
import java.time.LocalDate;
import java.time.LocalDateTime;

public record ChallengeResponse(
        Long id,
        Long householdId,
        String title,
        String description,
        Double targetKwh,
        Integer creditReward,
        LocalDate startDate,
        LocalDate endDate,
        String status,
        LocalDateTime createdAt,
        LocalDateTime completedAt
) {
    public static ChallengeResponse from(EnergyChallenge c) {
        return new ChallengeResponse(
                c.getId(), c.getHousehold().getId(), c.getTitle(), c.getDescription(),
                c.getTargetKwh(), c.getCreditReward(),
                c.getStartDate(), c.getEndDate(),
                c.getStatus(), c.getCreatedAt(), c.getCompletedAt());
    }
}

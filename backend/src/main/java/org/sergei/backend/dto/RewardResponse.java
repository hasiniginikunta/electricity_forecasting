package org.sergei.backend.dto;

import org.sergei.backend.entity.Reward;

import java.time.LocalDateTime;

public record RewardResponse(Long id, Long householdId, Integer credits, String reason, LocalDateTime createdAt) {
    public static RewardResponse from(Reward r) {
        return new RewardResponse(r.getId(), r.getHousehold().getId(), r.getCredits(), r.getReason(), r.getCreatedAt());
    }
}

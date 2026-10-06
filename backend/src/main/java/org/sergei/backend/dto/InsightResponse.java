package org.sergei.backend.dto;

import org.sergei.backend.entity.Insight;

import java.time.LocalDateTime;

public record InsightResponse(Long id, Long householdId, String type, String message, LocalDateTime createdAt) {
    public static InsightResponse from(Insight i) {
        return new InsightResponse(i.getId(), i.getHousehold().getId(), i.getType(), i.getMessage(), i.getCreatedAt());
    }
}

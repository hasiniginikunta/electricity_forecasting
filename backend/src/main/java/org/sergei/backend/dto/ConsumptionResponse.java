package org.sergei.backend.dto;

import org.sergei.backend.entity.Consumption;

public record ConsumptionResponse(Long id, Long householdId, String billingMonth, Double kwhConsumed) {
    public static ConsumptionResponse from(Consumption c) {
        return new ConsumptionResponse(c.getId(), c.getHousehold().getId(), c.getBillingMonth(), c.getKwhConsumed());
    }
}

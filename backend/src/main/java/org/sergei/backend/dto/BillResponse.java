package org.sergei.backend.dto;

import org.sergei.backend.entity.Bill;

public record BillResponse(Long id, Long householdId, String billingMonth, Double unitsConsumed, Double billAmount) {
    public static BillResponse from(Bill b) {
        return new BillResponse(b.getId(), b.getHousehold().getId(), b.getBillingMonth(), b.getUnitsConsumed(), b.getBillAmount());
    }
}

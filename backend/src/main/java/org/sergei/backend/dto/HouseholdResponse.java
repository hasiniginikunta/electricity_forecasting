package org.sergei.backend.dto;

import org.sergei.backend.entity.Household;

public record HouseholdResponse(Long id, Long userId, Integer householdSize, String city, String state, String homeType) {
    public static HouseholdResponse from(Household h) {
        return new HouseholdResponse(h.getId(), h.getUser().getId(), h.getHouseholdSize(), h.getCity(), h.getState(), h.getHomeType());
    }
}

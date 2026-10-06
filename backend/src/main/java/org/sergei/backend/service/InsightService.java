package org.sergei.backend.service;

import org.sergei.backend.dto.InsightRequest;
import org.sergei.backend.dto.InsightResponse;
import org.sergei.backend.entity.Household;
import org.sergei.backend.entity.Insight;
import org.sergei.backend.exception.ResourceNotFoundException;
import org.sergei.backend.repository.HouseholdRepository;
import org.sergei.backend.repository.InsightRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class InsightService {

    private final InsightRepository insightRepository;
    private final HouseholdRepository householdRepository;
    private final AuthorizationService authorizationService;

    public InsightService(InsightRepository insightRepository,
                          HouseholdRepository householdRepository,
                          AuthorizationService authorizationService) {
        this.insightRepository = insightRepository;
        this.householdRepository = householdRepository;
        this.authorizationService = authorizationService;
    }

    /**
     * Saves an insight after verifying the caller owns the target household.
     */
    public InsightResponse save(InsightRequest req) {
        authorizationService.requireHouseholdOwnership(req.householdId());
        Household h = householdRepository.findById(req.householdId())
                .orElseThrow(() -> new ResourceNotFoundException(
                        "Household not found with id: " + req.householdId()));
        Insight i = new Insight();
        i.setHousehold(h);
        i.setType(req.type());
        i.setMessage(req.message());
        return InsightResponse.from(insightRepository.save(i));
    }

    /**
     * Returns insights for the given household after verifying ownership.
     */
    public List<InsightResponse> getByHousehold(Long householdId) {
        authorizationService.requireHouseholdOwnership(householdId);
        return insightRepository.findByHouseholdIdOrderByCreatedAtDesc(householdId)
                .stream().map(InsightResponse::from).toList();
    }
}

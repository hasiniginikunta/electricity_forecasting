package org.sergei.backend.service;

import org.sergei.backend.dto.ConsumptionRequest;
import org.sergei.backend.dto.ConsumptionResponse;
import org.sergei.backend.entity.Consumption;
import org.sergei.backend.entity.Household;
import org.sergei.backend.exception.ResourceNotFoundException;
import org.sergei.backend.repository.ConsumptionRepository;
import org.sergei.backend.repository.HouseholdRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class ConsumptionService {

    private final ConsumptionRepository consumptionRepository;
    private final HouseholdRepository householdRepository;
    private final AuthorizationService authorizationService;

    public ConsumptionService(ConsumptionRepository consumptionRepository,
                              HouseholdRepository householdRepository,
                              AuthorizationService authorizationService) {
        this.consumptionRepository = consumptionRepository;
        this.householdRepository = householdRepository;
        this.authorizationService = authorizationService;
    }

    /**
     * Records a consumption entry.  Verifies that the authenticated user owns
     * the household supplied in the request before saving.
     */
    public ConsumptionResponse save(ConsumptionRequest req) {
        authorizationService.requireHouseholdOwnership(req.householdId());
        Household h = householdRepository.findById(req.householdId())
                .orElseThrow(() -> new ResourceNotFoundException(
                        "Household not found with id: " + req.householdId()));
        Consumption c = new Consumption();
        c.setHousehold(h);
        c.setBillingMonth(req.billingMonth());
        c.setKwhConsumed(req.kwhConsumed());
        return ConsumptionResponse.from(consumptionRepository.save(c));
    }

    /**
     * Returns consumption records for the given household.
     * Verifies that the authenticated user owns that household first.
     */
    public List<ConsumptionResponse> getByHousehold(Long householdId) {
        authorizationService.requireHouseholdOwnership(householdId);
        return consumptionRepository.findByHouseholdIdOrderByBillingMonthAsc(householdId)
                .stream().map(ConsumptionResponse::from).toList();
    }
}

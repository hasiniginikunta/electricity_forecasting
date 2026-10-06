package org.sergei.backend.service;

import org.sergei.backend.dto.BillRequest;
import org.sergei.backend.dto.BillResponse;
import org.sergei.backend.entity.Bill;
import org.sergei.backend.entity.Household;
import org.sergei.backend.exception.ResourceNotFoundException;
import org.sergei.backend.repository.BillRepository;
import org.sergei.backend.repository.HouseholdRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class BillService {

    private final BillRepository billRepository;
    private final HouseholdRepository householdRepository;
    private final AuthorizationService authorizationService;

    public BillService(BillRepository billRepository,
                       HouseholdRepository householdRepository,
                       AuthorizationService authorizationService) {
        this.billRepository = billRepository;
        this.householdRepository = householdRepository;
        this.authorizationService = authorizationService;
    }

    /**
     * Saves a bill entry after verifying the caller owns the target household.
     */
    public BillResponse save(BillRequest req) {
        authorizationService.requireHouseholdOwnership(req.householdId());
        Household h = householdRepository.findById(req.householdId())
                .orElseThrow(() -> new ResourceNotFoundException(
                        "Household not found with id: " + req.householdId()));
        Bill b = new Bill();
        b.setHousehold(h);
        b.setBillingMonth(req.billingMonth());
        b.setUnitsConsumed(req.unitsConsumed());
        b.setBillAmount(req.billAmount());
        return BillResponse.from(billRepository.save(b));
    }

    /**
     * Returns bills for the given household after verifying ownership.
     */
    public List<BillResponse> getByHousehold(Long householdId) {
        authorizationService.requireHouseholdOwnership(householdId);
        return billRepository.findByHouseholdIdOrderByBillingMonthAsc(householdId)
                .stream().map(BillResponse::from).toList();
    }
}

package org.sergei.backend.service;

import org.sergei.backend.dto.RewardRequest;
import org.sergei.backend.dto.RewardResponse;
import org.sergei.backend.entity.Household;
import org.sergei.backend.entity.Reward;
import org.sergei.backend.exception.ResourceNotFoundException;
import org.sergei.backend.repository.HouseholdRepository;
import org.sergei.backend.repository.RewardRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class RewardService {

    private final RewardRepository rewardRepository;
    private final HouseholdRepository householdRepository;
    private final AuthorizationService authorizationService;

    public RewardService(RewardRepository rewardRepository,
                         HouseholdRepository householdRepository,
                         AuthorizationService authorizationService) {
        this.rewardRepository = rewardRepository;
        this.householdRepository = householdRepository;
        this.authorizationService = authorizationService;
    }

    /**
     * Saves a reward after verifying the caller owns the target household.
     */
    public RewardResponse save(RewardRequest req) {
        authorizationService.requireHouseholdOwnership(req.householdId());
        Household h = householdRepository.findById(req.householdId())
                .orElseThrow(() -> new ResourceNotFoundException(
                        "Household not found with id: " + req.householdId()));
        Reward r = new Reward();
        r.setHousehold(h);
        r.setCredits(req.credits());
        r.setReason(req.reason());
        return RewardResponse.from(rewardRepository.save(r));
    }

    /**
     * Returns rewards for the given household after verifying ownership.
     */
    public List<RewardResponse> getByHousehold(Long householdId) {
        authorizationService.requireHouseholdOwnership(householdId);
        return rewardRepository.findByHouseholdIdOrderByCreatedAtDesc(householdId)
                .stream().map(RewardResponse::from).toList();
    }
}

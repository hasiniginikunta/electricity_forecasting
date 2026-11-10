package org.sergei.backend.service;

import org.sergei.backend.dto.ChallengeRequest;
import org.sergei.backend.dto.ChallengeResponse;
import org.sergei.backend.dto.RewardRequest;
import org.sergei.backend.dto.RewardResponse;
import org.sergei.backend.entity.EnergyChallenge;
import org.sergei.backend.entity.Household;
import org.sergei.backend.entity.Reward;
import org.sergei.backend.exception.ResourceNotFoundException;
import org.sergei.backend.repository.EnergyChallengeRepository;
import org.sergei.backend.repository.HouseholdRepository;
import org.sergei.backend.repository.RewardRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Service
public class RewardService {

    private final RewardRepository rewardRepository;
    private final HouseholdRepository householdRepository;
    private final EnergyChallengeRepository challengeRepository;
    private final AuthorizationService authorizationService;

    public RewardService(RewardRepository rewardRepository,
                         HouseholdRepository householdRepository,
                         EnergyChallengeRepository challengeRepository,
                         AuthorizationService authorizationService) {
        this.rewardRepository = rewardRepository;
        this.householdRepository = householdRepository;
        this.challengeRepository = challengeRepository;
        this.authorizationService = authorizationService;
    }

    // ── Legacy reward endpoints ──────────────────────────────────────────────

    public RewardResponse save(RewardRequest req) {
        authorizationService.requireHouseholdOwnership(req.householdId());
        Household h = getHousehold(req.householdId());
        return RewardResponse.from(rewardRepository.save(buildReward(h, req.credits(), req.reason())));
    }

    public List<RewardResponse> getByHousehold(Long householdId) {
        authorizationService.requireHouseholdOwnership(householdId);
        return rewardRepository.findByHouseholdIdOrderByCreatedAtDesc(householdId)
                .stream().map(RewardResponse::from).toList();
    }

    /** Total credit balance for a household. */
    public Map<String, Object> getCreditBalance(Long householdId) {
        authorizationService.requireHouseholdOwnership(householdId);
        int total = rewardRepository.findByHouseholdIdOrderByCreatedAtDesc(householdId)
                .stream().mapToInt(Reward::getCredits).sum();
        return Map.of("householdId", householdId, "totalCredits", total);
    }

    // ── Challenge lifecycle ──────────────────────────────────────────────────

    public ChallengeResponse createChallenge(ChallengeRequest req) {
        authorizationService.requireHouseholdOwnership(req.householdId());
        Household h = getHousehold(req.householdId());

        EnergyChallenge c = new EnergyChallenge();
        c.setHousehold(h);
        c.setTitle(req.title());
        c.setDescription(req.description());
        c.setTargetKwh(req.targetKwh());
        c.setCreditReward(req.creditReward());
        c.setStartDate(req.startDate());
        c.setEndDate(req.endDate());
        c.setStatus("ACTIVE");
        return ChallengeResponse.from(challengeRepository.save(c));
    }

    public List<ChallengeResponse> getChallenges(Long householdId) {
        authorizationService.requireHouseholdOwnership(householdId);
        return challengeRepository.findByHouseholdIdOrderByCreatedAtDesc(householdId)
                .stream().map(ChallengeResponse::from).toList();
    }

    public List<ChallengeResponse> getActiveChallenges(Long householdId) {
        authorizationService.requireHouseholdOwnership(householdId);
        return challengeRepository.findByHouseholdIdAndStatus(householdId, "ACTIVE")
                .stream().map(ChallengeResponse::from).toList();
    }

    /**
     * Marks a challenge COMPLETED and awards credits to the household.
     * Idempotent: re-completing an already-completed challenge is a no-op.
     */
    @Transactional
    public ChallengeResponse completeChallenge(Long challengeId) {
        EnergyChallenge c = challengeRepository.findById(challengeId)
                .orElseThrow(() -> new ResourceNotFoundException("Challenge not found: " + challengeId));
        authorizationService.requireHouseholdOwnership(c.getHousehold().getId());

        if ("COMPLETED".equals(c.getStatus())) return ChallengeResponse.from(c);

        c.setStatus("COMPLETED");
        c.setCompletedAt(LocalDateTime.now());
        challengeRepository.save(c);

        // Award credits
        rewardRepository.save(buildReward(c.getHousehold(), c.getCreditReward(),
                "Challenge completed: " + c.getTitle()));

        return ChallengeResponse.from(c);
    }

    @Transactional
    public ChallengeResponse cancelChallenge(Long challengeId) {
        EnergyChallenge c = challengeRepository.findById(challengeId)
                .orElseThrow(() -> new ResourceNotFoundException("Challenge not found: " + challengeId));
        authorizationService.requireHouseholdOwnership(c.getHousehold().getId());
        c.setStatus("CANCELLED");
        return ChallengeResponse.from(challengeRepository.save(c));
    }

    // ── Helpers ──────────────────────────────────────────────────────────────

    private Household getHousehold(Long id) {
        return householdRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Household not found: " + id));
    }

    private Reward buildReward(Household h, int credits, String reason) {
        Reward r = new Reward();
        r.setHousehold(h);
        r.setCredits(credits);
        r.setReason(reason);
        return r;
    }
}

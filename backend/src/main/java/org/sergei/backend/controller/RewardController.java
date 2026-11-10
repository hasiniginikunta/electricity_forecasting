package org.sergei.backend.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.sergei.backend.dto.ChallengeRequest;
import org.sergei.backend.dto.ChallengeResponse;
import org.sergei.backend.dto.RewardRequest;
import org.sergei.backend.dto.RewardResponse;
import org.sergei.backend.service.RewardService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@Tag(name = "Rewards & Challenges", description = "Virtual energy credits and gamification challenges")
@RestController
@RequestMapping("/api/rewards")
public class RewardController {

    private final RewardService rewardService;

    public RewardController(RewardService rewardService) {
        this.rewardService = rewardService;
    }

    // ── Credits ──────────────────────────────────────────────────────────────

    @Operation(summary = "Award credits manually")
    @ApiResponse(responseCode = "201", description = "Credits awarded")
    @PreAuthorize("isAuthenticated()")
    @PostMapping
    ResponseEntity<RewardResponse> create(@Valid @RequestBody RewardRequest req) {
        return ResponseEntity.status(HttpStatus.CREATED).body(rewardService.save(req));
    }

    @Operation(summary = "Get credit transaction history for a household")
    @ApiResponse(responseCode = "200", description = "Transaction history")
    @ApiResponse(responseCode = "403", description = "Access denied")
    @PreAuthorize("isAuthenticated()")
    @GetMapping("/household/{householdId}")
    ResponseEntity<List<RewardResponse>> getByHousehold(@PathVariable Long householdId) {
        return ResponseEntity.ok(rewardService.getByHousehold(householdId));
    }

    @Operation(summary = "Get total credit balance for a household")
    @ApiResponse(responseCode = "200", description = "Credit balance")
    @ApiResponse(responseCode = "403", description = "Access denied")
    @PreAuthorize("isAuthenticated()")
    @GetMapping("/household/{householdId}/balance")
    ResponseEntity<Map<String, Object>> getBalance(@PathVariable Long householdId) {
        return ResponseEntity.ok(rewardService.getCreditBalance(householdId));
    }

    // ── Challenges ───────────────────────────────────────────────────────────

    @Operation(summary = "Create an energy challenge")
    @ApiResponse(responseCode = "201", description = "Challenge created")
    @PreAuthorize("isAuthenticated()")
    @PostMapping("/challenges")
    ResponseEntity<ChallengeResponse> createChallenge(@Valid @RequestBody ChallengeRequest req) {
        return ResponseEntity.status(HttpStatus.CREATED).body(rewardService.createChallenge(req));
    }

    @Operation(summary = "List all challenges for a household")
    @ApiResponse(responseCode = "200", description = "All challenges")
    @ApiResponse(responseCode = "403", description = "Access denied")
    @PreAuthorize("isAuthenticated()")
    @GetMapping("/challenges/household/{householdId}")
    ResponseEntity<List<ChallengeResponse>> getChallenges(@PathVariable Long householdId) {
        return ResponseEntity.ok(rewardService.getChallenges(householdId));
    }

    @Operation(summary = "List active challenges for a household")
    @ApiResponse(responseCode = "200", description = "Active challenges")
    @PreAuthorize("isAuthenticated()")
    @GetMapping("/challenges/household/{householdId}/active")
    ResponseEntity<List<ChallengeResponse>> getActiveChallenges(@PathVariable Long householdId) {
        return ResponseEntity.ok(rewardService.getActiveChallenges(householdId));
    }

    @Operation(summary = "Complete a challenge and award credits",
               description = "Marks the challenge COMPLETED, awards the configured credit reward, and returns the updated challenge.")
    @ApiResponse(responseCode = "200", description = "Challenge completed and credits awarded")
    @ApiResponse(responseCode = "404", description = "Challenge not found")
    @PreAuthorize("isAuthenticated()")
    @PostMapping("/challenges/{challengeId}/complete")
    ResponseEntity<ChallengeResponse> completeChallenge(@PathVariable Long challengeId) {
        return ResponseEntity.ok(rewardService.completeChallenge(challengeId));
    }

    @Operation(summary = "Cancel a challenge")
    @ApiResponse(responseCode = "200", description = "Challenge cancelled")
    @ApiResponse(responseCode = "404", description = "Challenge not found")
    @PreAuthorize("isAuthenticated()")
    @PostMapping("/challenges/{challengeId}/cancel")
    ResponseEntity<ChallengeResponse> cancelChallenge(@PathVariable Long challengeId) {
        return ResponseEntity.ok(rewardService.cancelChallenge(challengeId));
    }
}

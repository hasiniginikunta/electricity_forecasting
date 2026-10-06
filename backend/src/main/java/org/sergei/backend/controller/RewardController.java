package org.sergei.backend.controller;

import jakarta.validation.Valid;

import org.sergei.backend.dto.RewardRequest;
import org.sergei.backend.dto.RewardResponse;
import org.sergei.backend.service.RewardService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/rewards")

public class RewardController {

    private final RewardService rewardService;
    public RewardController(RewardService rewardService) {
    	this.rewardService =rewardService;
    }

    @PostMapping
    ResponseEntity<RewardResponse> create(@Valid @RequestBody RewardRequest req) {
        return ResponseEntity.status(HttpStatus.CREATED).body(rewardService.save(req));
    }

    @GetMapping("/household/{householdId}")
    ResponseEntity<List<RewardResponse>> getByHousehold(@PathVariable Long householdId) {
        return ResponseEntity.ok(rewardService.getByHousehold(householdId));
    }
}

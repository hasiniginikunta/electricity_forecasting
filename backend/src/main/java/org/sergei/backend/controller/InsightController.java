package org.sergei.backend.controller;

import jakarta.validation.Valid;

import org.sergei.backend.dto.InsightRequest;
import org.sergei.backend.dto.InsightResponse;
import org.sergei.backend.service.InsightService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/insights")

public class InsightController {

    private final InsightService insightService;
    public InsightController(InsightService insightService) {
    	this.insightService=insightService;
    }

    @PostMapping
    ResponseEntity<InsightResponse> create(@Valid @RequestBody InsightRequest req) {
        return ResponseEntity.status(HttpStatus.CREATED).body(insightService.save(req));
    }

    @GetMapping("/household/{householdId}")
    ResponseEntity<List<InsightResponse>> getByHousehold(@PathVariable Long householdId) {
        return ResponseEntity.ok(insightService.getByHousehold(householdId));
    }
}

package org.sergei.backend.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.sergei.backend.dto.InsightRequest;
import org.sergei.backend.dto.InsightResponse;
import org.sergei.backend.service.InsightService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Tag(name = "Insights", description = "ML-driven energy insights and recommendations")
@RestController
@RequestMapping("/api/insights")
public class InsightController {

    private final InsightService insightService;

    public InsightController(InsightService insightService) {
        this.insightService = insightService;
    }

    @Operation(summary = "Manually create an insight")
    @ApiResponse(responseCode = "201", description = "Insight created")
    @PreAuthorize("isAuthenticated()")
    @PostMapping
    ResponseEntity<InsightResponse> create(@Valid @RequestBody InsightRequest req) {
        return ResponseEntity.status(HttpStatus.CREATED).body(insightService.save(req));
    }

    @Operation(summary = "Get all insights for a household")
    @ApiResponse(responseCode = "200", description = "List of insights")
    @ApiResponse(responseCode = "403", description = "Access denied")
    @PreAuthorize("isAuthenticated()")
    @GetMapping("/household/{householdId}")
    ResponseEntity<List<InsightResponse>> getByHousehold(@PathVariable Long householdId) {
        return ResponseEntity.ok(insightService.getByHousehold(householdId));
    }

    @Operation(summary = "Generate ML-driven insights for a household",
               description = "Runs peak detection, anomaly/benchmark/savings ML analysis and persists all generated insights.")
    @ApiResponse(responseCode = "201", description = "Insights generated and saved")
    @ApiResponse(responseCode = "403", description = "Access denied")
    @ApiResponse(responseCode = "404", description = "Household not found")
    @PreAuthorize("isAuthenticated()")
    @PostMapping("/household/{householdId}/generate")
    ResponseEntity<List<InsightResponse>> generate(@PathVariable Long householdId) {
        return ResponseEntity.status(HttpStatus.CREATED).body(insightService.generateInsights(householdId));
    }
}

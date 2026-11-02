package org.sergei.backend.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.sergei.backend.dto.BenchmarkRequest;
import org.sergei.backend.dto.BenchmarkResponse;
import org.sergei.backend.service.BenchmarkService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Tag(name = "Benchmarks", description = "Peer consumption benchmark endpoints")
@RestController
@RequestMapping("/api/benchmarks")
public class BenchmarkController {

    private final BenchmarkService benchmarkService;

    public BenchmarkController(BenchmarkService benchmarkService) {
        this.benchmarkService = benchmarkService;
    }

    @Operation(summary = "Ingest a benchmark record")
    @ApiResponse(responseCode = "201", description = "Benchmark created")
    @PreAuthorize("isAuthenticated()")
    @PostMapping
    ResponseEntity<BenchmarkResponse> create(@Valid @RequestBody BenchmarkRequest req) {
        return ResponseEntity.status(HttpStatus.CREATED).body(benchmarkService.save(req));
    }

    @Operation(summary = "List all benchmark records")
    @ApiResponse(responseCode = "200", description = "All benchmarks")
    @PreAuthorize("isAuthenticated()")
    @GetMapping
    ResponseEntity<List<BenchmarkResponse>> getAll() {
        return ResponseEntity.ok(benchmarkService.getAll());
    }

    @Operation(summary = "Match a benchmark by household segment",
               description = "Returns the benchmark record matching city, state, household size group and home type.")
    @ApiResponse(responseCode = "200", description = "Benchmark matched")
    @ApiResponse(responseCode = "404", description = "No benchmark found for the given criteria")
    @PreAuthorize("isAuthenticated()")
    @GetMapping("/match")
    ResponseEntity<BenchmarkResponse> match(
            @RequestParam String city,
            @RequestParam String state,
            @RequestParam String householdSizeGroup,
            @RequestParam String homeType) {
        return ResponseEntity.ok(benchmarkService.match(city, state, householdSizeGroup, homeType));
    }
}

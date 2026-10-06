package org.sergei.backend.controller;

import jakarta.validation.Valid;

import org.sergei.backend.dto.BenchmarkRequest;
import org.sergei.backend.dto.BenchmarkResponse;
import org.sergei.backend.service.BenchmarkService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/benchmarks")

public class BenchmarkController {

    private final BenchmarkService benchmarkService;
    public BenchmarkController(BenchmarkService benchmarkService) {
    	this.benchmarkService=benchmarkService;
    }

    @PostMapping
    ResponseEntity<BenchmarkResponse> create(@Valid @RequestBody BenchmarkRequest req) {
        return ResponseEntity.status(HttpStatus.CREATED).body(benchmarkService.save(req));
    }

    @GetMapping
    ResponseEntity<List<BenchmarkResponse>> getAll() {
        return ResponseEntity.ok(benchmarkService.getAll());
    }

    @GetMapping("/match")
    ResponseEntity<BenchmarkResponse> match(
            @RequestParam String city,
            @RequestParam String state,
            @RequestParam String householdSizeGroup,
            @RequestParam String homeType) {
        return ResponseEntity.ok(benchmarkService.match(city, state, householdSizeGroup, homeType));
    }
}

package org.sergei.backend.controller;

import jakarta.validation.Valid;

import org.sergei.backend.dto.HouseholdRequest;
import org.sergei.backend.dto.HouseholdResponse;
import org.sergei.backend.service.HouseholdService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/households")

public class HouseholdController {

    private final HouseholdService householdService;
    public HouseholdController(HouseholdService householdService) {
    	this.householdService =householdService;
    }
    @PostMapping
    ResponseEntity<HouseholdResponse> create(@Valid @RequestBody HouseholdRequest req) {
        return ResponseEntity.status(HttpStatus.CREATED).body(householdService.create(req));
    }

    @GetMapping("/{id}")
    ResponseEntity<HouseholdResponse> getById(@PathVariable Long id) {
        return ResponseEntity.ok(householdService.getById(id));
    }

    @PutMapping("/{id}")
    ResponseEntity<HouseholdResponse> update(@PathVariable Long id, @Valid @RequestBody HouseholdRequest req) {
        return ResponseEntity.ok(householdService.update(id, req));
    }
}

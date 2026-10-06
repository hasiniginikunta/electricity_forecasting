package org.sergei.backend.controller;

import jakarta.validation.Valid;

import org.sergei.backend.dto.ConsumptionRequest;
import org.sergei.backend.dto.ConsumptionResponse;
import org.sergei.backend.service.ConsumptionService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/consumption")

public class ConsumptionController {

    private final ConsumptionService consumptionService;
    public ConsumptionController(ConsumptionService consumptionService) {
    	this.consumptionService =consumptionService;
    }
    @PostMapping
    ResponseEntity<ConsumptionResponse> create(@Valid @RequestBody ConsumptionRequest req) {
        return ResponseEntity.status(HttpStatus.CREATED).body(consumptionService.save(req));
    }

    @GetMapping("/household/{householdId}")
    ResponseEntity<List<ConsumptionResponse>> getByHousehold(@PathVariable Long householdId) {
        return ResponseEntity.ok(consumptionService.getByHousehold(householdId));
    }
}

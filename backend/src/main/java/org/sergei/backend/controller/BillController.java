package org.sergei.backend.controller;

import jakarta.validation.Valid;

import org.sergei.backend.dto.BillRequest;
import org.sergei.backend.dto.BillResponse;
import org.sergei.backend.service.BillService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/bills")

public class BillController {

    private final BillService billService;
    public BillController(BillService billService) {
    	this.billService =billService;
    }

    @PostMapping
    ResponseEntity<BillResponse> create(@Valid @RequestBody BillRequest req) {
        return ResponseEntity.status(HttpStatus.CREATED).body(billService.save(req));
    }

    @GetMapping("/household/{householdId}")
    ResponseEntity<List<BillResponse>> getByHousehold(@PathVariable Long householdId) {
        return ResponseEntity.ok(billService.getByHousehold(householdId));
    }
}

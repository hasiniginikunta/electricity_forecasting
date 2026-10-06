package org.sergei.backend.controller;

import jakarta.validation.Valid;

import org.sergei.backend.dto.ForecastRequest;
import org.sergei.backend.dto.ForecastResponse;
import org.sergei.backend.service.ForecastService;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.List;

@RestController
@RequestMapping("/api/forecasts")
public class ForecastController {

    private final ForecastService forecastService;
    public ForecastController(ForecastService forecastService) {
    	this.forecastService= forecastService;
    }
    @PostMapping
    ResponseEntity<ForecastResponse> create(@Valid @RequestBody ForecastRequest req) {
        return ResponseEntity.status(HttpStatus.CREATED).body(forecastService.save(req));
    }

    @GetMapping("/state/{state}")
    ResponseEntity<List<ForecastResponse>> getByState(@PathVariable String state) {
        return ResponseEntity.ok(forecastService.getByState(state));
    }

    @GetMapping("/state/{state}/date/{date}")
    ResponseEntity<ForecastResponse> getByStateAndDate(
            @PathVariable String state,
            @PathVariable @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate date) {
        return ResponseEntity.ok(forecastService.getByStateAndDate(state, date));
    }
}

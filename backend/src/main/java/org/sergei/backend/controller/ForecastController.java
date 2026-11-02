package org.sergei.backend.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.sergei.backend.dto.ForecastRequest;
import org.sergei.backend.dto.ForecastResponse;
import org.sergei.backend.service.ForecastService;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.List;

@Tag(name = "Forecasts", description = "Electricity demand, solar and wind forecast endpoints")
@RestController
@RequestMapping("/api/forecasts")
public class ForecastController {

    private final ForecastService forecastService;

    public ForecastController(ForecastService forecastService) {
        this.forecastService = forecastService;
    }

    @Operation(summary = "Ingest a forecast record")
    @ApiResponse(responseCode = "201", description = "Forecast created")
    @PreAuthorize("isAuthenticated()")
    @PostMapping
    ResponseEntity<ForecastResponse> create(@Valid @RequestBody ForecastRequest req) {
        return ResponseEntity.status(HttpStatus.CREATED).body(forecastService.save(req));
    }

    @Operation(summary = "Get all forecasts for a state")
    @ApiResponse(responseCode = "200", description = "List of forecasts")
    @PreAuthorize("isAuthenticated()")
    @GetMapping("/state/{state}")
    ResponseEntity<List<ForecastResponse>> getByState(@PathVariable String state) {
        return ResponseEntity.ok(forecastService.getByState(state));
    }

    @Operation(summary = "Get forecast for a specific state and date")
    @ApiResponse(responseCode = "200", description = "Forecast found")
    @ApiResponse(responseCode = "404", description = "Forecast not found")
    @PreAuthorize("isAuthenticated()")
    @GetMapping("/state/{state}/date/{date}")
    ResponseEntity<ForecastResponse> getByStateAndDate(
            @PathVariable String state,
            @PathVariable @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate date) {
        return ResponseEntity.ok(forecastService.getByStateAndDate(state, date));
    }

    @Operation(summary = "Run ML forecast pipeline for a state and date",
               description = "Invokes the Python ML model, computes net demand and renewable share, persists and returns the result.")
    @ApiResponse(responseCode = "201", description = "ML forecast computed and saved")
    @ApiResponse(responseCode = "404", description = "ML service unavailable")
    @PreAuthorize("isAuthenticated()")
    @PostMapping("/ml")
    ResponseEntity<ForecastResponse> runMlForecast(
            @RequestParam String state,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate date) {
        return ResponseEntity.status(HttpStatus.CREATED).body(forecastService.runMlForecast(state, date));
    }
}

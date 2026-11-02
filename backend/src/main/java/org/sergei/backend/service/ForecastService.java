package org.sergei.backend.service;

import org.sergei.backend.dto.ForecastRequest;
import org.sergei.backend.dto.ForecastResponse;
import org.sergei.backend.entity.Forecast;
import org.sergei.backend.exception.ResourceNotFoundException;
import org.sergei.backend.repository.ForecastRepository;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

@Service
public class ForecastService {

    private final ForecastRepository forecastRepository;
    private final MlBridgeService mlBridgeService;

    public ForecastService(ForecastRepository forecastRepository, MlBridgeService mlBridgeService) {
        this.forecastRepository = forecastRepository;
        this.mlBridgeService = mlBridgeService;
    }

    /** Persist a forecast record (manual / pipeline ingestion path). */
    public ForecastResponse save(ForecastRequest req) {
        Forecast f = new Forecast();
        f.setState(req.state());
        f.setForecastDate(req.forecastDate());
        f.setDemandMw(req.demandMw());
        f.setSolarCapacityFactor(req.solarCapacityFactor());
        f.setWindCapacityFactor(req.windCapacityFactor());
        f.setNetDemandMw(computeNetDemand(req.demandMw(), req.solarCapacityFactor(), req.windCapacityFactor()));
        f.setRenewableShare(computeRenewableShare(req.demandMw(), req.solarCapacityFactor(), req.windCapacityFactor()));
        f.setRiskLevel(req.riskLevel());
        return ForecastResponse.from(forecastRepository.save(f));
    }

    public List<ForecastResponse> getByState(String state) {
        return forecastRepository.findByState(state).stream().map(ForecastResponse::from).toList();
    }

    public ForecastResponse getByStateAndDate(String state, LocalDate date) {
        return forecastRepository.findByStateAndForecastDate(state, date)
                .map(ForecastResponse::from)
                .orElseThrow(() -> new ResourceNotFoundException(
                        "Forecast not found for state=" + state + " date=" + date));
    }

    /**
     * Calls the ML pipeline, computes derived metrics, persists and returns the result.
     * Net Demand  = max(0, demand - (solar + wind))
     * Renewable % = (solar + wind) / totalGeneration * 100
     */
    public ForecastResponse runMlForecast(String state, LocalDate date) {
        Map<String, Object> raw = mlBridgeService.runForecastInference(state, date.toString());
        if (raw.containsKey("error")) {
            throw new ResourceNotFoundException("ML forecast unavailable: " + raw.get("detail"));
        }

        double demand = toDouble(raw.get("demand_mw"));
        double solar  = toDouble(raw.get("solar_capacity_factor"));
        double wind   = toDouble(raw.get("wind_capacity_factor"));

        Forecast f = new Forecast();
        f.setState(state);
        f.setForecastDate(date);
        f.setDemandMw(demand);
        f.setSolarCapacityFactor(solar);
        f.setWindCapacityFactor(wind);
        f.setNetDemandMw(computeNetDemand(demand, solar, wind));
        f.setRenewableShare(computeRenewableShare(demand, solar, wind));
        f.setRiskLevel((String) raw.getOrDefault("risk_level", "UNKNOWN"));
        return ForecastResponse.from(forecastRepository.save(f));
    }

    // ── Derived metric formulas ──────────────────────────────────────────────

    /** Net Demand = max(0, electricityDemand - (solar + wind)) */
    public double computeNetDemand(Double demand, Double solar, Double wind) {
        if (demand == null || solar == null || wind == null) return 0.0;
        return Math.max(0.0, demand - (solar + wind));
    }

    /** Renewable Share (%) = (solar + wind) / totalGeneration * 100 */
    public double computeRenewableShare(Double demand, Double solar, Double wind) {
        if (demand == null || solar == null || wind == null) return 0.0;
        double total = demand + solar + wind;
        if (total == 0) return 0.0;
        return ((solar + wind) / total) * 100.0;
    }

    private double toDouble(Object val) {
        if (val instanceof Number n) return n.doubleValue();
        if (val instanceof String s) return Double.parseDouble(s);
        return 0.0;
    }
}

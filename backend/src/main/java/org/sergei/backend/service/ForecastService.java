package org.sergei.backend.service;

import org.sergei.backend.dto.ForecastRequest;
import org.sergei.backend.dto.ForecastResponse;
import org.sergei.backend.entity.Forecast;
import org.sergei.backend.exception.ResourceNotFoundException;
import org.sergei.backend.repository.ForecastRepository;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.List;

@Service
public class ForecastService {

    private final ForecastRepository forecastRepository;

    public ForecastService(ForecastRepository forecastRepository) {
        this.forecastRepository = forecastRepository;
    }

    public ForecastResponse save(ForecastRequest req) {
        Forecast f = new Forecast();
        f.setState(req.state());
        f.setForecastDate(req.forecastDate());
        f.setDemandMw(req.demandMw());
        f.setSolarCapacityFactor(req.solarCapacityFactor());
        f.setWindCapacityFactor(req.windCapacityFactor());
        f.setNetDemandMw(req.netDemandMw());
        f.setRenewableShare(req.renewableShare());
        f.setRiskLevel(req.riskLevel());
        return ForecastResponse.from(forecastRepository.save(f));
    }

    public List<ForecastResponse> getByState(String state) {
        return forecastRepository.findByState(state).stream().map(ForecastResponse::from).toList();
    }

    public ForecastResponse getByStateAndDate(String state, LocalDate date) {
        return forecastRepository.findByStateAndForecastDate(state, date)
                .map(ForecastResponse::from)
                .orElseThrow(() -> new ResourceNotFoundException("Forecast not found for state=" + state + " date=" + date));
    }
}

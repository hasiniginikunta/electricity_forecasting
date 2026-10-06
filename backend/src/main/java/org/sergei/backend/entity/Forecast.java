package org.sergei.backend.entity;

import jakarta.persistence.*;
import java.time.LocalDate;

@Entity
@Table(name = "forecasts",
        uniqueConstraints = @UniqueConstraint(
                name = "uq_forecasts_state_date",
                columnNames = {"state", "forecast_date"}))
public class Forecast {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String state;

    @Column(nullable = false)
    private LocalDate forecastDate;

    private Double demandMw;
    private Double solarCapacityFactor;
    private Double windCapacityFactor;
    private Double netDemandMw;
    private Double renewableShare;
    private String riskLevel;

    public Forecast() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getState() { return state; }
    public void setState(String state) { this.state = state; }

    public LocalDate getForecastDate() { return forecastDate; }
    public void setForecastDate(LocalDate forecastDate) { this.forecastDate = forecastDate; }

    public Double getDemandMw() { return demandMw; }
    public void setDemandMw(Double demandMw) { this.demandMw = demandMw; }

    public Double getSolarCapacityFactor() { return solarCapacityFactor; }
    public void setSolarCapacityFactor(Double solarCapacityFactor) { this.solarCapacityFactor = solarCapacityFactor; }

    public Double getWindCapacityFactor() { return windCapacityFactor; }
    public void setWindCapacityFactor(Double windCapacityFactor) { this.windCapacityFactor = windCapacityFactor; }

    public Double getNetDemandMw() { return netDemandMw; }
    public void setNetDemandMw(Double netDemandMw) { this.netDemandMw = netDemandMw; }

    public Double getRenewableShare() { return renewableShare; }
    public void setRenewableShare(Double renewableShare) { this.renewableShare = renewableShare; }

    public String getRiskLevel() { return riskLevel; }
    public void setRiskLevel(String riskLevel) { this.riskLevel = riskLevel; }
}

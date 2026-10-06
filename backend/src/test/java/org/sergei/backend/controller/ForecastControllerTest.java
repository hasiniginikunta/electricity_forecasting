package org.sergei.backend.controller;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.sergei.backend.dto.ForecastResponse;
import org.sergei.backend.exception.ResourceNotFoundException;
import org.sergei.backend.service.ForecastService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.context.WebApplicationContext;

import java.time.LocalDate;
import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.MOCK)
class ForecastControllerTest {

    @Autowired WebApplicationContext wac;
    @MockitoBean ForecastService forecastService;

    MockMvc mockMvc;

    @BeforeEach
    void setup() {
        mockMvc = MockMvcBuilders.webAppContextSetup(wac).build();
    }

    private ForecastResponse sample() {
        return new ForecastResponse(1L, "Telangana", LocalDate.of(2026, 10, 6),
                8500.0, 0.62, 0.31, 5400.0, 0.36, "HIGH");
    }

    @Test
    void create_validRequest_returns201() throws Exception {
        when(forecastService.save(any())).thenReturn(sample());

        mockMvc.perform(post("/api/forecasts")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"state\":\"Telangana\",\"forecastDate\":\"2026-10-06\",\"demandMw\":8500.0," +
                                 "\"solarCapacityFactor\":0.62,\"windCapacityFactor\":0.31," +
                                 "\"netDemandMw\":5400.0,\"renewableShare\":0.36,\"riskLevel\":\"HIGH\"}"))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.state").value("Telangana"))
                .andExpect(jsonPath("$.riskLevel").value("HIGH"));
    }

    @Test
    void create_missingState_returns400() throws Exception {
        mockMvc.perform(post("/api/forecasts")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"state\":\"\",\"forecastDate\":\"2026-10-06\",\"demandMw\":8500.0}"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void getByState_returns200() throws Exception {
        when(forecastService.getByState("Telangana")).thenReturn(List.of(sample()));

        mockMvc.perform(get("/api/forecasts/state/Telangana"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].demandMw").value(8500.0));
    }

    @Test
    void getByStateAndDate_notFound_returns404() throws Exception {
        when(forecastService.getByStateAndDate("Telangana", LocalDate.of(2026, 1, 1)))
                .thenThrow(new ResourceNotFoundException("Forecast not found"));

        mockMvc.perform(get("/api/forecasts/state/Telangana/date/2026-01-01"))
                .andExpect(status().isNotFound());
    }
}

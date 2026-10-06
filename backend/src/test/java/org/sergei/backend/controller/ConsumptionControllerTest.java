package org.sergei.backend.controller;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.sergei.backend.dto.ConsumptionResponse;
import org.sergei.backend.service.ConsumptionService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.context.WebApplicationContext;

import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.MOCK)
class ConsumptionControllerTest {

    @Autowired WebApplicationContext wac;
    @MockitoBean ConsumptionService consumptionService;

    MockMvc mockMvc;

    @BeforeEach
    void setup() {
        mockMvc = MockMvcBuilders.webAppContextSetup(wac).build();
    }

    @Test
    void create_validRequest_returns201() throws Exception {
        ConsumptionResponse resp = new ConsumptionResponse(1L, 1L, "2026-09", 210.0);
        when(consumptionService.save(any())).thenReturn(resp);

        mockMvc.perform(post("/api/consumption")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"householdId\":1,\"billingMonth\":\"2026-09\",\"kwhConsumed\":210.0}"))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.kwhConsumed").value(210.0));
    }

    @Test
    void create_negativeKwh_returns400() throws Exception {
        mockMvc.perform(post("/api/consumption")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"householdId\":1,\"billingMonth\":\"2026-09\",\"kwhConsumed\":-10.0}"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void getByHousehold_returns200() throws Exception {
        when(consumptionService.getByHousehold(1L))
                .thenReturn(List.of(new ConsumptionResponse(1L, 1L, "2026-09", 210.0)));

        mockMvc.perform(get("/api/consumption/household/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].billingMonth").value("2026-09"));
    }
}

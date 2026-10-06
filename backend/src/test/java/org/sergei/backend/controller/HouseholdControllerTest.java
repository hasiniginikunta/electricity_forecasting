package org.sergei.backend.controller;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.sergei.backend.dto.HouseholdResponse;
import org.sergei.backend.exception.ResourceNotFoundException;
import org.sergei.backend.service.HouseholdService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.context.WebApplicationContext;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.MOCK)
class HouseholdControllerTest {

    @Autowired WebApplicationContext wac;
    @MockitoBean HouseholdService householdService;

    MockMvc mockMvc;

    @BeforeEach
    void setup() {
        mockMvc = MockMvcBuilders.webAppContextSetup(wac).build();
    }

    private static final String VALID_JSON =
            "{\"userId\":1,\"householdSize\":3,\"city\":\"Hyderabad\",\"state\":\"Telangana\",\"homeType\":\"FLAT\"}";

    private HouseholdResponse sample() {
        return new HouseholdResponse(1L, 1L, 3, "Hyderabad", "Telangana", "FLAT");
    }

    @Test
    void create_validRequest_returns201() throws Exception {
        when(householdService.create(any())).thenReturn(sample());

        mockMvc.perform(post("/api/households")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(VALID_JSON))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.city").value("Hyderabad"));
    }

    @Test
    void create_missingCity_returns400() throws Exception {
        mockMvc.perform(post("/api/households")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"userId\":1,\"householdSize\":3,\"city\":\"\",\"state\":\"Telangana\",\"homeType\":\"FLAT\"}"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void getById_exists_returns200() throws Exception {
        when(householdService.getById(1L)).thenReturn(sample());

        mockMvc.perform(get("/api/households/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.state").value("Telangana"));
    }

    @Test
    void getById_notFound_returns404() throws Exception {
        when(householdService.getById(99L))
                .thenThrow(new ResourceNotFoundException("Household not found with id: 99"));

        mockMvc.perform(get("/api/households/99"))
                .andExpect(status().isNotFound());
    }

    @Test
    void update_validRequest_returns200() throws Exception {
        HouseholdResponse updated = new HouseholdResponse(1L, 1L, 4, "Chennai", "Tamil Nadu", "INDEPENDENT_HOUSE");
        when(householdService.update(eq(1L), any())).thenReturn(updated);

        mockMvc.perform(put("/api/households/1")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(VALID_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.city").value("Chennai"));
    }
}

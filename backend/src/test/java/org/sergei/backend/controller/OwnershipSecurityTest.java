package org.sergei.backend.controller;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.sergei.backend.config.JwtService;
import org.sergei.backend.entity.AppUser;
import org.sergei.backend.entity.Household;
import org.sergei.backend.repository.AppUserRepository;
import org.sergei.backend.repository.HouseholdRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.context.WebApplicationContext;

import static org.springframework.security.test.web.servlet.setup.SecurityMockMvcConfigurers.springSecurity;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Integration tests that exercise ownership and authentication enforcement
 * end-to-end: real Spring Security filter chain, real JWT tokens, H2 database.
 *
 * Two users are created per test:
 *   - userA  owns householdA
 *   - userB  owns householdB
 *
 * Each scenario verifies one of:
 *   - No JWT                     → 401 Unauthorized
 *   - JWT for owner              → 2xx success
 *   - JWT for a different user   → 403 Forbidden
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.MOCK)
@Transactional
class OwnershipSecurityTest {

    @Autowired WebApplicationContext wac;
    @Autowired AppUserRepository userRepository;
    @Autowired HouseholdRepository householdRepository;
    @Autowired JwtService jwtService;
    @Autowired PasswordEncoder passwordEncoder;

    MockMvc mockMvc;

    // Two users and two households set up fresh for every test (rolled back by @Transactional)
    AppUser userA;
    AppUser userB;
    Household householdA;
    Household householdB;
    String tokenA;
    String tokenB;

    @BeforeEach
    void setUp() {
        // Apply the full Spring Security filter chain so JwtAuthFilter runs
        mockMvc = MockMvcBuilders
                .webAppContextSetup(wac)
                .apply(springSecurity())
                .build();

        userA = createUser("alice@test.com", "Alice");
        userB = createUser("bob@test.com", "Bob");

        householdA = createHousehold(userA);
        householdB = createHousehold(userB);

        tokenA = jwtService.generateToken(userA.getId(), userA.getEmail());
        tokenB = jwtService.generateToken(userB.getId(), userB.getEmail());
    }

    // =========================================================================
    // Unauthenticated → 401
    // =========================================================================

    @Test
    void unauthenticated_getHousehold_returns401() throws Exception {
        mockMvc.perform(get("/api/households/" + householdA.getId()))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void unauthenticated_getConsumption_returns401() throws Exception {
        mockMvc.perform(get("/api/consumption/household/" + householdA.getId()))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void unauthenticated_getBills_returns401() throws Exception {
        mockMvc.perform(get("/api/bills/household/" + householdA.getId()))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void unauthenticated_getInsights_returns401() throws Exception {
        mockMvc.perform(get("/api/insights/household/" + householdA.getId()))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void unauthenticated_getRewards_returns401() throws Exception {
        mockMvc.perform(get("/api/rewards/household/" + householdA.getId()))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void unauthenticated_getUser_returns401() throws Exception {
        mockMvc.perform(get("/api/users/" + userA.getId()))
                .andExpect(status().isUnauthorized());
    }

    // =========================================================================
    // Authenticated owner → 2xx success
    // =========================================================================

    @Test
    void owner_getHousehold_returns200() throws Exception {
        mockMvc.perform(get("/api/households/" + householdA.getId())
                        .header("Authorization", "Bearer " + tokenA))
                .andExpect(status().isOk());
    }

    @Test
    void owner_getConsumption_returns200() throws Exception {
        mockMvc.perform(get("/api/consumption/household/" + householdA.getId())
                        .header("Authorization", "Bearer " + tokenA))
                .andExpect(status().isOk());
    }

    @Test
    void owner_getBills_returns200() throws Exception {
        mockMvc.perform(get("/api/bills/household/" + householdA.getId())
                        .header("Authorization", "Bearer " + tokenA))
                .andExpect(status().isOk());
    }

    @Test
    void owner_getInsights_returns200() throws Exception {
        mockMvc.perform(get("/api/insights/household/" + householdA.getId())
                        .header("Authorization", "Bearer " + tokenA))
                .andExpect(status().isOk());
    }

    @Test
    void owner_getRewards_returns200() throws Exception {
        mockMvc.perform(get("/api/rewards/household/" + householdA.getId())
                        .header("Authorization", "Bearer " + tokenA))
                .andExpect(status().isOk());
    }

    @Test
    void owner_getUser_returns200() throws Exception {
        mockMvc.perform(get("/api/users/" + userA.getId())
                        .header("Authorization", "Bearer " + tokenA))
                .andExpect(status().isOk());
    }

    // =========================================================================
    // Authenticated but wrong user → 403 Forbidden
    // =========================================================================

    @Test
    void nonOwner_getHousehold_returns403() throws Exception {
        // userB tries to read userA's household
        mockMvc.perform(get("/api/households/" + householdA.getId())
                        .header("Authorization", "Bearer " + tokenB))
                .andExpect(status().isForbidden());
    }

    @Test
    void nonOwner_updateHousehold_returns403() throws Exception {
        mockMvc.perform(put("/api/households/" + householdA.getId())
                        .header("Authorization", "Bearer " + tokenB)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"userId\":2,\"householdSize\":5,\"city\":\"Chennai\"," +
                                 "\"state\":\"Tamil Nadu\",\"homeType\":\"FLAT\"}"))
                .andExpect(status().isForbidden());
    }

    @Test
    void nonOwner_postConsumption_returns403() throws Exception {
        // userB sends householdId belonging to userA
        mockMvc.perform(post("/api/consumption")
                        .header("Authorization", "Bearer " + tokenB)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"householdId\":" + householdA.getId() +
                                 ",\"billingMonth\":\"2026-09\",\"kwhConsumed\":150.0}"))
                .andExpect(status().isForbidden());
    }

    @Test
    void nonOwner_getConsumption_returns403() throws Exception {
        mockMvc.perform(get("/api/consumption/household/" + householdA.getId())
                        .header("Authorization", "Bearer " + tokenB))
                .andExpect(status().isForbidden());
    }

    @Test
    void nonOwner_postBill_returns403() throws Exception {
        mockMvc.perform(post("/api/bills")
                        .header("Authorization", "Bearer " + tokenB)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"householdId\":" + householdA.getId() +
                                 ",\"billingMonth\":\"2026-09\",\"unitsConsumed\":150.0,\"billAmount\":900.0}"))
                .andExpect(status().isForbidden());
    }

    @Test
    void nonOwner_getBills_returns403() throws Exception {
        mockMvc.perform(get("/api/bills/household/" + householdA.getId())
                        .header("Authorization", "Bearer " + tokenB))
                .andExpect(status().isForbidden());
    }

    @Test
    void nonOwner_postInsight_returns403() throws Exception {
        mockMvc.perform(post("/api/insights")
                        .header("Authorization", "Bearer " + tokenB)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"householdId\":" + householdA.getId() +
                                 ",\"type\":\"SAVING\",\"message\":\"Reduce AC usage\"}"))
                .andExpect(status().isForbidden());
    }

    @Test
    void nonOwner_getInsights_returns403() throws Exception {
        mockMvc.perform(get("/api/insights/household/" + householdA.getId())
                        .header("Authorization", "Bearer " + tokenB))
                .andExpect(status().isForbidden());
    }

    @Test
    void nonOwner_postReward_returns403() throws Exception {
        mockMvc.perform(post("/api/rewards")
                        .header("Authorization", "Bearer " + tokenB)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"householdId\":" + householdA.getId() +
                                 ",\"credits\":50,\"reason\":\"Saved energy\"}"))
                .andExpect(status().isForbidden());
    }

    @Test
    void nonOwner_getRewards_returns403() throws Exception {
        mockMvc.perform(get("/api/rewards/household/" + householdA.getId())
                        .header("Authorization", "Bearer " + tokenB))
                .andExpect(status().isForbidden());
    }

    @Test
    void nonOwner_getUser_returns403() throws Exception {
        // userB tries to fetch userA's account
        mockMvc.perform(get("/api/users/" + userA.getId())
                        .header("Authorization", "Bearer " + tokenB))
                .andExpect(status().isForbidden());
    }

    // =========================================================================
    // Helpers
    // =========================================================================

    private AppUser createUser(String email, String name) {
        AppUser u = new AppUser();
        u.setEmail(email);
        u.setName(name);
        u.setPassword(passwordEncoder.encode("password123"));
        return userRepository.save(u);
    }

    private Household createHousehold(AppUser owner) {
        Household h = new Household();
        h.setUser(owner);
        h.setHouseholdSize(3);
        h.setCity("Hyderabad");
        h.setState("Telangana");
        h.setHomeType("FLAT");
        return householdRepository.save(h);
    }
}

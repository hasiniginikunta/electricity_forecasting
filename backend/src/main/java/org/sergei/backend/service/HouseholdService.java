package org.sergei.backend.service;

import org.sergei.backend.dto.HouseholdRequest;
import org.sergei.backend.dto.HouseholdResponse;
import org.sergei.backend.entity.AppUser;
import org.sergei.backend.entity.Household;
import org.sergei.backend.exception.ResourceNotFoundException;
import org.sergei.backend.repository.HouseholdRepository;
import org.springframework.stereotype.Service;

@Service
public class HouseholdService {

    private final HouseholdRepository householdRepository;
    private final AuthorizationService authorizationService;

    public HouseholdService(HouseholdRepository householdRepository,
                            AuthorizationService authorizationService) {
        this.householdRepository = householdRepository;
        this.authorizationService = authorizationService;
    }

    /**
     * Creates a household for the currently authenticated user.
     * The userId in the request body is intentionally ignored — ownership is
     * derived from the JWT so a client cannot forge it.
     */
    public HouseholdResponse create(HouseholdRequest req) {
        AppUser caller = authorizationService.getAuthenticatedUser();
        Household h = new Household();
        h.setUser(caller);
        h.setHouseholdSize(req.householdSize());
        h.setCity(req.city());
        h.setState(req.state());
        h.setHomeType(req.homeType());
        return HouseholdResponse.from(householdRepository.save(h));
    }

    /**
     * Returns the household only if the authenticated user owns it.
     * Throws 404 if the household does not exist, 403 if it belongs to another user.
     */
    public HouseholdResponse getById(Long id) {
        Household h = find(id);
        authorizationService.requireHouseholdOwnership(h.getId());
        return HouseholdResponse.from(h);
    }

    /**
     * Updates the household only if the authenticated user owns it.
     * The userId in the request body is ignored for the same reason as create().
     */
    public HouseholdResponse update(Long id, HouseholdRequest req) {
        Household h = find(id);
        authorizationService.requireHouseholdOwnership(h.getId());
        h.setHouseholdSize(req.householdSize());
        h.setCity(req.city());
        h.setState(req.state());
        h.setHomeType(req.homeType());
        return HouseholdResponse.from(householdRepository.save(h));
    }

    private Household find(Long id) {
        return householdRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Household not found with id: " + id));
    }
}

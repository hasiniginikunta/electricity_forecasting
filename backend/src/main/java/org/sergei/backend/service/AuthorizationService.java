package org.sergei.backend.service;

import org.sergei.backend.entity.AppUser;
import org.sergei.backend.entity.Household;
import org.sergei.backend.exception.ResourceNotFoundException;
import org.sergei.backend.repository.AppUserRepository;
import org.sergei.backend.repository.HouseholdRepository;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;

/**
 * Central service for resolving the currently authenticated user and
 * enforcing resource-ownership checks.
 *
 * <p>Ownership model:
 * <ul>
 *   <li>An {@link AppUser} owns a {@link Household} when {@code household.user.id == user.id}.
 *   <li>A user owns household-scoped data (Consumption, Bill, Insight, Reward) when the
 *       target {@code householdId} belongs to their household.
 * </ul>
 *
 * <p>All denial decisions throw {@link AccessDeniedException}, which is mapped to
 * HTTP 403 by {@code GlobalExceptionHandler}.
 */
@Service
public class AuthorizationService {

    private final AppUserRepository userRepository;
    private final HouseholdRepository householdRepository;

    public AuthorizationService(AppUserRepository userRepository,
                                HouseholdRepository householdRepository) {
        this.userRepository = userRepository;
        this.householdRepository = householdRepository;
    }

    // -------------------------------------------------------------------------
    // Principal resolution
    // -------------------------------------------------------------------------

    /**
     * Returns the {@link AppUser} entity for the currently authenticated principal.
     * The principal username is the email set by {@code JwtAuthFilter}.
     *
     * @throws AccessDeniedException if there is no authenticated principal
     */
    public AppUser getAuthenticatedUser() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || !auth.isAuthenticated() || "anonymousUser".equals(auth.getPrincipal())) {
            throw new AccessDeniedException("No authenticated user");
        }
        String email = auth.getName();   // JwtAuthFilter stores email as the principal name
        return userRepository.findByEmail(email)
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + email));
    }

    // -------------------------------------------------------------------------
    // Ownership checks — throw 403 on violation
    // -------------------------------------------------------------------------

    /**
     * Asserts that the authenticated user's ID matches {@code targetUserId}.
     * Use this when protecting user-scoped endpoints such as {@code GET /api/users/{id}}.
     */
    public void requireSameUser(Long targetUserId) {
        AppUser caller = getAuthenticatedUser();
        if (!caller.getId().equals(targetUserId)) {
            throw new AccessDeniedException("Access denied");
        }
    }

    /**
     * Asserts that the authenticated user owns the household identified by
     * {@code householdId}.  Ownership is established when
     * {@code household.user.id == authenticatedUser.id}.
     *
     * @throws ResourceNotFoundException if the household does not exist
     * @throws AccessDeniedException     if the caller does not own the household
     */
    public void requireHouseholdOwnership(Long householdId) {
        AppUser caller = getAuthenticatedUser();
        Household household = householdRepository.findById(householdId)
                .orElseThrow(() -> new ResourceNotFoundException(
                        "Household not found with id: " + householdId));
        if (!household.getUser().getId().equals(caller.getId())) {
            throw new AccessDeniedException("Access denied");
        }
    }

    /**
     * Returns the household that belongs to the authenticated user, or throws
     * {@link ResourceNotFoundException} if the user has not yet created one.
     * Use this for POST endpoints where the household is identified by
     * the caller's identity rather than a client-supplied ID.
     */
    public Household getOwnedHousehold() {
        AppUser caller = getAuthenticatedUser();
        return householdRepository.findByUserId(caller.getId())
                .orElseThrow(() -> new ResourceNotFoundException(
                        "No household found for the authenticated user"));
    }
}

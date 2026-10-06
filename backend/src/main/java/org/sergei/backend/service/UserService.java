package org.sergei.backend.service;

import org.sergei.backend.config.JwtService;
import org.sergei.backend.dto.LoginRequest;
import org.sergei.backend.dto.LoginResponse;
import org.sergei.backend.dto.RegisterRequest;
import org.sergei.backend.dto.UserResponse;
import org.sergei.backend.entity.AppUser;
import org.sergei.backend.exception.DuplicateEmailException;
import org.sergei.backend.exception.ResourceNotFoundException;
import org.sergei.backend.repository.AppUserRepository;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class UserService {

    private final AppUserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;
    private final AuthenticationManager authenticationManager;
    private final AuthorizationService authorizationService;

    public UserService(AppUserRepository userRepository,
                       PasswordEncoder passwordEncoder,
                       JwtService jwtService,
                       AuthenticationManager authenticationManager,
                       AuthorizationService authorizationService) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
        this.authenticationManager = authenticationManager;
        this.authorizationService = authorizationService;
    }

    public UserResponse register(RegisterRequest req) {
        if (userRepository.existsByEmail(req.email())) {
            throw new DuplicateEmailException(req.email());
        }
        AppUser user = new AppUser();
        user.setName(req.name());
        user.setEmail(req.email());
        user.setPassword(passwordEncoder.encode(req.password()));
        return UserResponse.from(userRepository.save(user));
    }

    public LoginResponse login(LoginRequest req) {
        authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(req.email(), req.password()));
        AppUser user = userRepository.findByEmail(req.email())
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + req.email()));
        String token = jwtService.generateToken(user.getId(), user.getEmail());
        return new LoginResponse(token, user.getId(), user.getName());
    }

    /**
     * Returns the user profile only if the authenticated user is requesting
     * their own account. Any other ID yields 403.
     */
    public UserResponse getById(Long id) {
        authorizationService.requireSameUser(id);
        return UserResponse.from(userRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("User not found with id: " + id)));
    }
}

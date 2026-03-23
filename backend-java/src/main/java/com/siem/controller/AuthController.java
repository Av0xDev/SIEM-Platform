package com.siem.controller;

import com.siem.config.JwtUtil;
import com.siem.dto.LoginRequest;
import com.siem.dto.LoginResponse;
import com.siem.dto.RegisterRequest;
import com.siem.dto.UserDTO;
import com.siem.model.AuditLog.Action;
import com.siem.service.AuditService;
import com.siem.service.UserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

@Slf4j
@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
@Tag(name = "Authentication", description = "Login, registration and token management endpoints")
public class AuthController {

    private final AuthenticationManager authenticationManager;
    private final UserService userService;
    private final JwtUtil jwtUtil;
    private final AuditService auditService;

    @Operation(summary = "Login", description = "Authenticate with username and password to receive a JWT token")
    @PostMapping("/login")
    public ResponseEntity<LoginResponse> login(
            @Valid @RequestBody LoginRequest request,
            HttpServletRequest httpRequest) {

        Authentication authentication = authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(request.getUsername(), request.getPassword()));

        UserDetails userDetails = (UserDetails) authentication.getPrincipal();
        String accessToken = jwtUtil.generateToken(userDetails);
        String refreshToken = jwtUtil.generateRefreshToken(userDetails);

        userService.recordLogin(request.getUsername());
        UserDTO userDTO = userService.getUserByUsername(request.getUsername());

        auditService.log(request.getUsername(), Action.LOGIN, "AUTH", null,
                "Successful login", httpRequest.getRemoteAddr(), true);

        LoginResponse response = LoginResponse.builder()
                .accessToken(accessToken)
                .refreshToken(refreshToken)
                .expiresIn(jwtUtil.getExpirationMs() / 1000)
                .userId(userDTO.getId())
                .username(userDTO.getUsername())
                .email(userDTO.getEmail())
                .role(userDTO.getRole())
                .build();

        return ResponseEntity.ok(response);
    }

    @Operation(summary = "Register", description = "Register a new user account")
    @PostMapping("/register")
    public ResponseEntity<UserDTO> register(
            @Valid @RequestBody RegisterRequest request,
            HttpServletRequest httpRequest) {

        var user = userService.register(request);
        UserDTO dto = UserDTO.fromEntity(user);

        auditService.log(request.getUsername(), Action.CREATE, "USER",
                String.valueOf(dto.getId()), "New user registered", httpRequest.getRemoteAddr(), true);

        return ResponseEntity.status(HttpStatus.CREATED).body(dto);
    }
}

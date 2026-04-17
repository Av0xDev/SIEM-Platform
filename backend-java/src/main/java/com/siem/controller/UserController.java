package com.siem.controller;

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
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
@Tag(name = "Users", description = "User management endpoints (Admin only)")
@PreAuthorize("hasRole('ADMIN')")
public class UserController {

    private final UserService userService;
    private final AuditService auditService;

    @Operation(summary = "List all users")
    @GetMapping
    public ResponseEntity<Page<UserDTO>> getUsers(
            @PageableDefault(size = 20, sort = "username") Pageable pageable) {
        return ResponseEntity.ok(userService.getAllUsers(pageable));
    }

    @Operation(summary = "Get user by ID")
    @GetMapping("/{id}")
    public ResponseEntity<UserDTO> getUser(@PathVariable Long id) {
        return ResponseEntity.ok(userService.getUserById(id));
    }

    @Operation(summary = "Update user")
    @PutMapping("/{id}")
    public ResponseEntity<UserDTO> updateUser(
            @PathVariable Long id,
            @Valid @RequestBody RegisterRequest request,
            Authentication auth,
            HttpServletRequest httpRequest) {

        UserDTO updated = userService.updateUser(id, request);
        auditService.log(auth.getName(), Action.UPDATE, "USER",
                String.valueOf(id), "User updated", httpRequest.getRemoteAddr(), true);
        return ResponseEntity.ok(updated);
    }

    @Operation(summary = "Enable or disable a user account")
    @PatchMapping("/{id}/enabled")
    public ResponseEntity<Void> toggleEnabled(
            @PathVariable Long id,
            @RequestParam boolean enabled,
            Authentication auth,
            HttpServletRequest httpRequest) {

        userService.toggleUserEnabled(id, enabled);
        auditService.log(auth.getName(), Action.UPDATE, "USER",
                String.valueOf(id), "User " + (enabled ? "enabled" : "disabled"),
                httpRequest.getRemoteAddr(), true);
        return ResponseEntity.noContent().build();
    }

    @Operation(summary = "Delete user")
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteUser(
            @PathVariable Long id,
            Authentication auth,
            HttpServletRequest httpRequest) {

        userService.deleteUser(id);
        auditService.log(auth.getName(), Action.DELETE, "USER",
                String.valueOf(id), "User deleted", httpRequest.getRemoteAddr(), true);
        return ResponseEntity.noContent().build();
    }

    @Operation(summary = "Get current user profile")
    @GetMapping("/me")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<UserDTO> getCurrentUser(Authentication auth) {
        return ResponseEntity.ok(userService.getUserByUsername(auth.getName()));
    }
}

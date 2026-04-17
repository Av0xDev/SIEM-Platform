package com.siem.controller;

import com.siem.dto.AlertDTO;
import com.siem.model.Alert.Severity;
import com.siem.model.Alert.Status;
import com.siem.model.AuditLog.Action;
import com.siem.service.AlertService;
import com.siem.service.AuditService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/alerts")
@RequiredArgsConstructor
@Tag(name = "Alerts", description = "Security alert management endpoints")
public class AlertController {

    private final AlertService alertService;
    private final AuditService auditService;

    @Operation(summary = "List alerts", description = "Retrieve paginated list of alerts with optional filtering")
    @ApiResponses({
            @ApiResponse(responseCode = "200", description = "Alerts retrieved successfully"),
            @ApiResponse(responseCode = "401", description = "Unauthorized")
    })
    @GetMapping
    public ResponseEntity<Page<AlertDTO>> getAlerts(
            @Parameter(description = "Filter by severity") @RequestParam(required = false) Severity severity,
            @Parameter(description = "Filter by status") @RequestParam(required = false) Status status,
            @Parameter(description = "Filter by assignee user ID") @RequestParam(required = false) Long assignedToId,
            @PageableDefault(size = 20, sort = "createdAt") Pageable pageable) {

        Page<AlertDTO> alerts;
        if (severity != null && status != null) {
            alerts = alertService.getAlertsBySeverityAndStatus(severity, status, pageable);
        } else if (severity != null) {
            alerts = alertService.getAlertsBySeverity(severity, pageable);
        } else if (status != null) {
            alerts = alertService.getAlertsByStatus(status, pageable);
        } else if (assignedToId != null) {
            alerts = alertService.getAlertsByAssignee(assignedToId, pageable);
        } else {
            alerts = alertService.getAllAlerts(pageable);
        }

        return ResponseEntity.ok(alerts);
    }

    @Operation(summary = "Get alert by ID")
    @GetMapping("/{id}")
    public ResponseEntity<AlertDTO> getAlert(@PathVariable Long id) {
        return ResponseEntity.ok(alertService.getAlertById(id));
    }

    @Operation(summary = "Get alerts by correlation ID", description = "Find all alerts sharing the same correlation ID")
    @GetMapping("/correlation/{correlationId}")
    public ResponseEntity<List<AlertDTO>> getByCorrelation(@PathVariable String correlationId) {
        return ResponseEntity.ok(alertService.getAlertsByCorrelationId(correlationId));
    }

    @Operation(summary = "Get alert statistics", description = "Returns counts by severity, status, and 24h trends")
    @GetMapping("/statistics")
    public ResponseEntity<Map<String, Object>> getStatistics() {
        return ResponseEntity.ok(alertService.getAlertStatistics());
    }

    @Operation(summary = "Create alert", description = "Create a new security alert")
    @ApiResponse(responseCode = "201", description = "Alert created")
    @PostMapping
    @PreAuthorize("hasAnyRole('ADMIN', 'ANALYST')")
    public ResponseEntity<AlertDTO> createAlert(
            @Valid @RequestBody AlertDTO dto,
            Authentication auth,
            HttpServletRequest request) {

        AlertDTO created = alertService.createAlert(dto);
        auditService.log(auth.getName(), Action.CREATE, "ALERT",
                String.valueOf(created.getId()), "Alert created: " + created.getTitle(),
                request.getRemoteAddr(), true);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }

    @Operation(summary = "Update alert")
    @PutMapping("/{id}")
    @PreAuthorize("hasAnyRole('ADMIN', 'ANALYST')")
    public ResponseEntity<AlertDTO> updateAlert(
            @PathVariable Long id,
            @Valid @RequestBody AlertDTO dto,
            Authentication auth,
            HttpServletRequest request) {

        AlertDTO updated = alertService.updateAlert(id, dto);
        auditService.log(auth.getName(), Action.UPDATE, "ALERT",
                String.valueOf(id), "Alert updated", request.getRemoteAddr(), true);
        return ResponseEntity.ok(updated);
    }

    @Operation(summary = "Update alert status")
    @PatchMapping("/{id}/status")
    @PreAuthorize("hasAnyRole('ADMIN', 'ANALYST')")
    public ResponseEntity<AlertDTO> updateStatus(
            @PathVariable Long id,
            @RequestParam Status status,
            Authentication auth,
            HttpServletRequest request) {

        AlertDTO updated = alertService.updateAlertStatus(id, status);
        auditService.log(auth.getName(), Action.UPDATE, "ALERT",
                String.valueOf(id), "Status changed to " + status, request.getRemoteAddr(), true);
        return ResponseEntity.ok(updated);
    }

    @Operation(summary = "Assign alert to user")
    @PatchMapping("/{id}/assign")
    @PreAuthorize("hasAnyRole('ADMIN', 'ANALYST')")
    public ResponseEntity<AlertDTO> assignAlert(
            @PathVariable Long id,
            @RequestParam Long userId,
            Authentication auth,
            HttpServletRequest request) {

        AlertDTO updated = alertService.assignAlert(id, userId);
        auditService.log(auth.getName(), Action.ASSIGN, "ALERT",
                String.valueOf(id), "Assigned to user " + userId, request.getRemoteAddr(), true);
        return ResponseEntity.ok(updated);
    }

    @Operation(summary = "Get alerts in date range")
    @GetMapping("/range")
    public ResponseEntity<Page<AlertDTO>> getByDateRange(
            @RequestParam LocalDateTime start,
            @RequestParam LocalDateTime end,
            @PageableDefault(size = 20) Pageable pageable) {
        return ResponseEntity.ok(alertService.getAlertsByDateRange(start, end, pageable));
    }

    @Operation(summary = "Delete alert")
    @DeleteMapping("/{id}")
    @PreAuthorize("hasAnyRole('ADMIN', 'ANALYST')")
    public ResponseEntity<Void> deleteAlert(
            @PathVariable Long id,
            Authentication auth,
            HttpServletRequest request) {

        alertService.deleteAlert(id);
        auditService.log(auth.getName(), Action.DELETE, "ALERT",
                String.valueOf(id), "Alert deleted", request.getRemoteAddr(), true);
        return ResponseEntity.noContent().build();
    }
}

package com.siem.controller;

import com.siem.dto.IncidentDTO;
import com.siem.model.Incident.Status;
import com.siem.model.AuditLog.Action;
import com.siem.service.AuditService;
import com.siem.service.IncidentService;
import io.swagger.v3.oas.annotations.Operation;
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

import java.util.Map;

@RestController
@RequestMapping("/api/incidents")
@RequiredArgsConstructor
@Tag(name = "Incidents", description = "Security incident management endpoints")
public class IncidentController {

    private final IncidentService incidentService;
    private final AuditService auditService;

    @Operation(summary = "List incidents")
    @GetMapping
    public ResponseEntity<Page<IncidentDTO>> getIncidents(
            @RequestParam(required = false) Status status,
            @PageableDefault(size = 20, sort = "createdAt") Pageable pageable) {

        Page<IncidentDTO> incidents = status != null
                ? incidentService.getIncidentsByStatus(status, pageable)
                : incidentService.getAllIncidents(pageable);
        return ResponseEntity.ok(incidents);
    }

    @Operation(summary = "Get incident by ID")
    @GetMapping("/{id}")
    public ResponseEntity<IncidentDTO> getIncident(@PathVariable Long id) {
        return ResponseEntity.ok(incidentService.getIncidentById(id));
    }

    @Operation(summary = "Get incident statistics")
    @GetMapping("/statistics")
    public ResponseEntity<Map<String, Object>> getStatistics() {
        return ResponseEntity.ok(Map.of(
                "activeIncidents", incidentService.getActiveIncidentCount()
        ));
    }

    @Operation(summary = "Create incident")
    @PostMapping
    @PreAuthorize("hasAnyRole('ADMIN', 'ANALYST')")
    public ResponseEntity<IncidentDTO> createIncident(
            @Valid @RequestBody IncidentDTO dto,
            Authentication auth,
            HttpServletRequest request) {

        IncidentDTO created = incidentService.createIncident(dto, auth.getName());
        auditService.log(auth.getName(), Action.CREATE, "INCIDENT",
                String.valueOf(created.getId()), "Incident created: " + created.getTitle(),
                request.getRemoteAddr(), true);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }

    @Operation(summary = "Update incident")
    @PutMapping("/{id}")
    @PreAuthorize("hasAnyRole('ADMIN', 'ANALYST')")
    public ResponseEntity<IncidentDTO> updateIncident(
            @PathVariable Long id,
            @Valid @RequestBody IncidentDTO dto,
            Authentication auth,
            HttpServletRequest request) {

        IncidentDTO updated = incidentService.updateIncident(id, dto);
        auditService.log(auth.getName(), Action.UPDATE, "INCIDENT",
                String.valueOf(id), "Incident updated", request.getRemoteAddr(), true);
        return ResponseEntity.ok(updated);
    }

    @Operation(summary = "Link an alert to this incident")
    @PostMapping("/{incidentId}/alerts/{alertId}")
    @PreAuthorize("hasAnyRole('ADMIN', 'ANALYST')")
    public ResponseEntity<IncidentDTO> linkAlert(
            @PathVariable Long incidentId,
            @PathVariable Long alertId,
            Authentication auth,
            HttpServletRequest request) {

        IncidentDTO updated = incidentService.linkAlert(incidentId, alertId);
        auditService.log(auth.getName(), Action.UPDATE, "INCIDENT",
                String.valueOf(incidentId), "Alert " + alertId + " linked",
                request.getRemoteAddr(), true);
        return ResponseEntity.ok(updated);
    }

    @Operation(summary = "Delete incident")
    @DeleteMapping("/{id}")
    @PreAuthorize("hasAnyRole('ADMIN', 'ANALYST')")
    public ResponseEntity<Void> deleteIncident(
            @PathVariable Long id,
            Authentication auth,
            HttpServletRequest request) {

        incidentService.deleteIncident(id);
        auditService.log(auth.getName(), Action.DELETE, "INCIDENT",
                String.valueOf(id), "Incident deleted", request.getRemoteAddr(), true);
        return ResponseEntity.noContent().build();
    }
}

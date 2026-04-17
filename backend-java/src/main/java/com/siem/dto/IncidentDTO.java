package com.siem.dto;

import com.siem.model.Incident;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class IncidentDTO {

    private Long id;

    @NotBlank(message = "Title is required")
    @Size(max = 255)
    private String title;

    private String description;

    @Builder.Default
    private Incident.Severity severity = Incident.Severity.MEDIUM;

    @Builder.Default
    private Incident.Status status = Incident.Status.OPEN;

    private String incidentType;
    private String impact;
    private String remediation;
    private String affectedSystems;

    private Long assignedToId;
    private String assignedToUsername;
    private Long createdById;
    private String createdByUsername;

    private int alertCount;
    private LocalDateTime resolvedAt;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public static IncidentDTO fromEntity(Incident incident) {
        IncidentDTO dto = IncidentDTO.builder()
                .id(incident.getId())
                .title(incident.getTitle())
                .description(incident.getDescription())
                .severity(incident.getSeverity())
                .status(incident.getStatus())
                .incidentType(incident.getIncidentType())
                .impact(incident.getImpact())
                .remediation(incident.getRemediation())
                .affectedSystems(incident.getAffectedSystems())
                .alertCount(incident.getAlerts() != null ? incident.getAlerts().size() : 0)
                .resolvedAt(incident.getResolvedAt())
                .createdAt(incident.getCreatedAt())
                .updatedAt(incident.getUpdatedAt())
                .build();

        if (incident.getAssignedTo() != null) {
            dto.setAssignedToId(incident.getAssignedTo().getId());
            dto.setAssignedToUsername(incident.getAssignedTo().getUsername());
        }
        if (incident.getCreatedBy() != null) {
            dto.setCreatedById(incident.getCreatedBy().getId());
            dto.setCreatedByUsername(incident.getCreatedBy().getUsername());
        }
        return dto;
    }
}

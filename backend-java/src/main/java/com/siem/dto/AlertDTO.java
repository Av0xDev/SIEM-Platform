package com.siem.dto;

import com.siem.model.Alert;
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
public class AlertDTO {

    private Long id;

    @NotBlank(message = "Title is required")
    @Size(max = 255, message = "Title must not exceed 255 characters")
    private String title;

    private String description;

    @Builder.Default
    private Alert.Severity severity = Alert.Severity.MEDIUM;

    @Builder.Default
    private Alert.Status status = Alert.Status.OPEN;

    private String sourceIp;
    private String destinationIp;
    private Integer sourcePort;
    private Integer destinationPort;
    private String eventType;
    private String rawLog;
    private String correlationId;
    private boolean falsePositive;

    private Long assignedToId;
    private String assignedToUsername;

    private Long incidentId;

    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public static AlertDTO fromEntity(Alert alert) {
        AlertDTO dto = AlertDTO.builder()
                .id(alert.getId())
                .title(alert.getTitle())
                .description(alert.getDescription())
                .severity(alert.getSeverity())
                .status(alert.getStatus())
                .sourceIp(alert.getSourceIp())
                .destinationIp(alert.getDestinationIp())
                .sourcePort(alert.getSourcePort())
                .destinationPort(alert.getDestinationPort())
                .eventType(alert.getEventType())
                .correlationId(alert.getCorrelationId())
                .falsePositive(alert.isFalsePositive())
                .createdAt(alert.getCreatedAt())
                .updatedAt(alert.getUpdatedAt())
                .build();

        if (alert.getAssignedTo() != null) {
            dto.setAssignedToId(alert.getAssignedTo().getId());
            dto.setAssignedToUsername(alert.getAssignedTo().getUsername());
        }
        if (alert.getIncident() != null) {
            dto.setIncidentId(alert.getIncident().getId());
        }
        return dto;
    }
}

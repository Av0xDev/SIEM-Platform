package com.siem.service;

import com.siem.dto.IncidentDTO;
import com.siem.exception.ResourceNotFoundException;
import com.siem.model.Alert;
import com.siem.model.Incident;
import com.siem.model.Incident.Status;
import com.siem.model.User;
import com.siem.repository.AlertRepository;
import com.siem.repository.IncidentRepository;
import com.siem.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class IncidentService {

    private final IncidentRepository incidentRepository;
    private final UserRepository userRepository;
    private final AlertRepository alertRepository;

    public Page<IncidentDTO> getAllIncidents(Pageable pageable) {
        return incidentRepository.findAll(pageable).map(IncidentDTO::fromEntity);
    }

    public Page<IncidentDTO> getIncidentsByStatus(Status status, Pageable pageable) {
        return incidentRepository.findByStatus(status, pageable).map(IncidentDTO::fromEntity);
    }

    public IncidentDTO getIncidentById(Long id) {
        return incidentRepository.findById(id)
                .map(IncidentDTO::fromEntity)
                .orElseThrow(() -> new ResourceNotFoundException("Incident", "id", id));
    }

    @Transactional
    public IncidentDTO createIncident(IncidentDTO dto, String creatorUsername) {
        User creator = userRepository.findByUsername(creatorUsername)
                .orElseThrow(() -> new ResourceNotFoundException("User", "username", creatorUsername));

        Incident incident = Incident.builder()
                .title(dto.getTitle())
                .description(dto.getDescription())
                .severity(dto.getSeverity() != null ? dto.getSeverity() : Incident.Severity.MEDIUM)
                .status(Status.OPEN)
                .incidentType(dto.getIncidentType())
                .impact(dto.getImpact())
                .remediation(dto.getRemediation())
                .affectedSystems(dto.getAffectedSystems())
                .createdBy(creator)
                .build();

        if (dto.getAssignedToId() != null) {
            userRepository.findById(dto.getAssignedToId()).ifPresent(incident::setAssignedTo);
        }

        Incident saved = incidentRepository.save(incident);
        log.info("Incident created: id={}, title={}", saved.getId(), saved.getTitle());
        return IncidentDTO.fromEntity(saved);
    }

    @Transactional
    public IncidentDTO updateIncident(Long id, IncidentDTO dto) {
        Incident incident = incidentRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Incident", "id", id));

        incident.setTitle(dto.getTitle());
        incident.setDescription(dto.getDescription());
        if (dto.getSeverity() != null) incident.setSeverity(dto.getSeverity());
        if (dto.getStatus() != null) {
            incident.setStatus(dto.getStatus());
            if (dto.getStatus() == Status.CLOSED || dto.getStatus() == Status.RECOVERED) {
                incident.setResolvedAt(LocalDateTime.now());
            }
        }
        incident.setIncidentType(dto.getIncidentType());
        incident.setImpact(dto.getImpact());
        incident.setRemediation(dto.getRemediation());
        incident.setAffectedSystems(dto.getAffectedSystems());

        if (dto.getAssignedToId() != null) {
            User assignee = userRepository.findById(dto.getAssignedToId())
                    .orElseThrow(() -> new ResourceNotFoundException("User", "id", dto.getAssignedToId()));
            incident.setAssignedTo(assignee);
        }

        return IncidentDTO.fromEntity(incidentRepository.save(incident));
    }

    @Transactional
    public IncidentDTO linkAlert(Long incidentId, Long alertId) {
        Incident incident = incidentRepository.findById(incidentId)
                .orElseThrow(() -> new ResourceNotFoundException("Incident", "id", incidentId));
        Alert alert = alertRepository.findById(alertId)
                .orElseThrow(() -> new ResourceNotFoundException("Alert", "id", alertId));

        alert.setIncident(incident);
        alertRepository.save(alert);
        log.info("Alert {} linked to incident {}", alertId, incidentId);
        return IncidentDTO.fromEntity(incident);
    }

    @Transactional
    public void deleteIncident(Long id) {
        if (!incidentRepository.existsById(id)) {
            throw new ResourceNotFoundException("Incident", "id", id);
        }
        incidentRepository.deleteById(id);
        log.info("Incident {} deleted", id);
    }

    public long getActiveIncidentCount() {
        return incidentRepository.countActiveIncidents();
    }
}

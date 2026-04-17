package com.siem.service;

import com.siem.dto.AlertDTO;
import com.siem.exception.ResourceNotFoundException;
import com.siem.model.Alert;
import com.siem.model.Alert.Severity;
import com.siem.model.Alert.Status;
import com.siem.model.User;
import com.siem.repository.AlertRepository;
import com.siem.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class AlertService {

    private final AlertRepository alertRepository;
    private final UserRepository userRepository;
    private final SimpMessagingTemplate messagingTemplate;

    public Page<AlertDTO> getAllAlerts(Pageable pageable) {
        return alertRepository.findAll(pageable).map(AlertDTO::fromEntity);
    }

    public Page<AlertDTO> getAlertsBySeverity(Severity severity, Pageable pageable) {
        return alertRepository.findBySeverity(severity, pageable).map(AlertDTO::fromEntity);
    }

    public Page<AlertDTO> getAlertsByStatus(Status status, Pageable pageable) {
        return alertRepository.findByStatus(status, pageable).map(AlertDTO::fromEntity);
    }

    public Page<AlertDTO> getAlertsBySeverityAndStatus(Severity severity, Status status, Pageable pageable) {
        return alertRepository.findBySeverityAndStatus(severity, status, pageable).map(AlertDTO::fromEntity);
    }

    public Page<AlertDTO> getAlertsByAssignee(Long userId, Pageable pageable) {
        return alertRepository.findByAssignedToId(userId, pageable).map(AlertDTO::fromEntity);
    }

    public Page<AlertDTO> getAlertsByDateRange(LocalDateTime start, LocalDateTime end, Pageable pageable) {
        return alertRepository.findByCreatedAtBetween(start, end, pageable).map(AlertDTO::fromEntity);
    }

    public AlertDTO getAlertById(Long id) {
        return alertRepository.findById(id)
                .map(AlertDTO::fromEntity)
                .orElseThrow(() -> new ResourceNotFoundException("Alert", "id", id));
    }

    public List<AlertDTO> getAlertsByCorrelationId(String correlationId) {
        return alertRepository.findByCorrelationId(correlationId)
                .stream().map(AlertDTO::fromEntity).toList();
    }

    @Transactional
    public AlertDTO createAlert(AlertDTO dto) {
        Alert alert = Alert.builder()
                .title(dto.getTitle())
                .description(dto.getDescription())
                .severity(dto.getSeverity() != null ? dto.getSeverity() : Severity.MEDIUM)
                .status(Status.OPEN)
                .sourceIp(dto.getSourceIp())
                .destinationIp(dto.getDestinationIp())
                .sourcePort(dto.getSourcePort())
                .destinationPort(dto.getDestinationPort())
                .eventType(dto.getEventType())
                .rawLog(dto.getRawLog())
                .correlationId(dto.getCorrelationId())
                .build();

        if (dto.getAssignedToId() != null) {
            User assignee = userRepository.findById(dto.getAssignedToId())
                    .orElseThrow(() -> new ResourceNotFoundException("User", "id", dto.getAssignedToId()));
            alert.setAssignedTo(assignee);
        }

        Alert saved = alertRepository.save(alert);
        log.info("Alert created: id={}, severity={}, title={}", saved.getId(), saved.getSeverity(), saved.getTitle());

        // Broadcast critical/high alerts via WebSocket
        if (saved.getSeverity() == Severity.CRITICAL || saved.getSeverity() == Severity.HIGH) {
            messagingTemplate.convertAndSend("/topic/alerts", AlertDTO.fromEntity(saved));
        }

        return AlertDTO.fromEntity(saved);
    }

    @Transactional
    public AlertDTO updateAlert(Long id, AlertDTO dto) {
        Alert alert = alertRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Alert", "id", id));

        alert.setTitle(dto.getTitle());
        alert.setDescription(dto.getDescription());
        if (dto.getSeverity() != null) alert.setSeverity(dto.getSeverity());
        if (dto.getStatus() != null) alert.setStatus(dto.getStatus());
        alert.setSourceIp(dto.getSourceIp());
        alert.setDestinationIp(dto.getDestinationIp());
        alert.setSourcePort(dto.getSourcePort());
        alert.setDestinationPort(dto.getDestinationPort());
        alert.setEventType(dto.getEventType());
        alert.setFalsePositive(dto.isFalsePositive());

        if (dto.getAssignedToId() != null) {
            User assignee = userRepository.findById(dto.getAssignedToId())
                    .orElseThrow(() -> new ResourceNotFoundException("User", "id", dto.getAssignedToId()));
            alert.setAssignedTo(assignee);
        } else {
            alert.setAssignedTo(null);
        }

        return AlertDTO.fromEntity(alertRepository.save(alert));
    }

    @Transactional
    public AlertDTO updateAlertStatus(Long id, Status status) {
        Alert alert = alertRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Alert", "id", id));
        alert.setStatus(status);
        return AlertDTO.fromEntity(alertRepository.save(alert));
    }

    @Transactional
    public AlertDTO assignAlert(Long alertId, Long userId) {
        Alert alert = alertRepository.findById(alertId)
                .orElseThrow(() -> new ResourceNotFoundException("Alert", "id", alertId));
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new ResourceNotFoundException("User", "id", userId));
        alert.setAssignedTo(user);
        alert.setStatus(Status.IN_PROGRESS);
        return AlertDTO.fromEntity(alertRepository.save(alert));
    }

    @Transactional
    public void deleteAlert(Long id) {
        if (!alertRepository.existsById(id)) {
            throw new ResourceNotFoundException("Alert", "id", id);
        }
        alertRepository.deleteById(id);
        log.info("Alert {} deleted", id);
    }

    public Map<String, Object> getAlertStatistics() {
        Map<String, Object> stats = new HashMap<>();
        stats.put("total", alertRepository.count());
        stats.put("open", alertRepository.countByStatus(Status.OPEN));
        stats.put("inProgress", alertRepository.countByStatus(Status.IN_PROGRESS));
        stats.put("resolved", alertRepository.countByStatus(Status.RESOLVED));
        stats.put("critical", alertRepository.countBySeverity(Severity.CRITICAL));
        stats.put("high", alertRepository.countBySeverity(Severity.HIGH));
        stats.put("medium", alertRepository.countBySeverity(Severity.MEDIUM));
        stats.put("low", alertRepository.countBySeverity(Severity.LOW));

        LocalDateTime last24h = LocalDateTime.now().minusHours(24);
        List<Object[]> trendData = alertRepository.countBySeveritySince(last24h);
        Map<String, Long> trend = new HashMap<>();
        for (Object[] row : trendData) {
            trend.put(row[0].toString(), (Long) row[1]);
        }
        stats.put("last24hBySeverity", trend);
        return stats;
    }
}

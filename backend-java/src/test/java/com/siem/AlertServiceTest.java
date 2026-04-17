package com.siem;

import com.siem.dto.AlertDTO;
import com.siem.exception.ResourceNotFoundException;
import com.siem.model.Alert;
import com.siem.model.Alert.Severity;
import com.siem.model.Alert.Status;
import com.siem.model.User;
import com.siem.repository.AlertRepository;
import com.siem.repository.UserRepository;
import com.siem.service.AlertService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.messaging.simp.SimpMessagingTemplate;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("AlertService Unit Tests")
class AlertServiceTest {

    @Mock
    private AlertRepository alertRepository;

    @Mock
    private UserRepository userRepository;

    @Mock
    private SimpMessagingTemplate messagingTemplate;

    @InjectMocks
    private AlertService alertService;

    private Alert sampleAlert;
    private User sampleUser;

    @BeforeEach
    void setUp() {
        sampleUser = User.builder()
                .id(1L)
                .username("analyst1")
                .email("analyst@siem.com")
                .passwordHash("hashed")
                .role(User.Role.ANALYST)
                .enabled(true)
                .build();

        sampleAlert = Alert.builder()
                .id(1L)
                .title("Suspicious SSH Login")
                .description("Multiple failed SSH attempts detected")
                .severity(Severity.HIGH)
                .status(Status.OPEN)
                .sourceIp("192.168.1.100")
                .destinationIp("10.0.0.5")
                .sourcePort(54321)
                .destinationPort(22)
                .eventType("AUTH_FAILURE")
                .createdAt(LocalDateTime.now())
                .updatedAt(LocalDateTime.now())
                .build();
    }

    // ==================== READ TESTS ====================

    @Test
    @DisplayName("getAllAlerts - returns paginated alerts as DTOs")
    void getAllAlerts_returnsPaginatedAlerts() {
        Pageable pageable = PageRequest.of(0, 10);
        Page<Alert> alertPage = new PageImpl<>(List.of(sampleAlert), pageable, 1);
        when(alertRepository.findAll(pageable)).thenReturn(alertPage);

        Page<AlertDTO> result = alertService.getAllAlerts(pageable);

        assertThat(result).isNotNull();
        assertThat(result.getTotalElements()).isEqualTo(1);
        assertThat(result.getContent().get(0).getTitle()).isEqualTo("Suspicious SSH Login");
        verify(alertRepository).findAll(pageable);
    }

    @Test
    @DisplayName("getAlertById - returns DTO when alert exists")
    void getAlertById_returnsDto_whenExists() {
        when(alertRepository.findById(1L)).thenReturn(Optional.of(sampleAlert));

        AlertDTO result = alertService.getAlertById(1L);

        assertThat(result).isNotNull();
        assertThat(result.getId()).isEqualTo(1L);
        assertThat(result.getTitle()).isEqualTo("Suspicious SSH Login");
        assertThat(result.getSeverity()).isEqualTo(Severity.HIGH);
        assertThat(result.getSourceIp()).isEqualTo("192.168.1.100");
    }

    @Test
    @DisplayName("getAlertById - throws ResourceNotFoundException when not found")
    void getAlertById_throwsException_whenNotFound() {
        when(alertRepository.findById(999L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> alertService.getAlertById(999L))
                .isInstanceOf(ResourceNotFoundException.class)
                .hasMessageContaining("Alert")
                .hasMessageContaining("999");
    }

    @Test
    @DisplayName("getAlertsBySeverity - filters by severity correctly")
    void getAlertsBySeverity_filtersBySeverity() {
        Pageable pageable = PageRequest.of(0, 10);
        Page<Alert> alertPage = new PageImpl<>(List.of(sampleAlert), pageable, 1);
        when(alertRepository.findBySeverity(Severity.HIGH, pageable)).thenReturn(alertPage);

        Page<AlertDTO> result = alertService.getAlertsBySeverity(Severity.HIGH, pageable);

        assertThat(result.getContent()).hasSize(1);
        assertThat(result.getContent().get(0).getSeverity()).isEqualTo(Severity.HIGH);
        verify(alertRepository).findBySeverity(Severity.HIGH, pageable);
    }

    @Test
    @DisplayName("getAlertsByCorrelationId - returns correlated alerts")
    void getAlertsByCorrelationId_returnsCorrelatedAlerts() {
        sampleAlert.setCorrelationId("CORR-001");
        Alert alert2 = Alert.builder()
                .id(2L).title("Related Alert").severity(Severity.MEDIUM)
                .status(Status.OPEN).correlationId("CORR-001").build();

        when(alertRepository.findByCorrelationId("CORR-001"))
                .thenReturn(List.of(sampleAlert, alert2));

        List<AlertDTO> result = alertService.getAlertsByCorrelationId("CORR-001");

        assertThat(result).hasSize(2);
        assertThat(result).allMatch(dto -> "CORR-001".equals(dto.getCorrelationId()));
    }

    // ==================== CREATE TESTS ====================

    @Test
    @DisplayName("createAlert - creates alert and returns DTO")
    void createAlert_createsAndReturnsDto() {
        AlertDTO inputDto = AlertDTO.builder()
                .title("Malware Detected")
                .description("Ransomware signature found")
                .severity(Severity.CRITICAL)
                .sourceIp("10.10.10.10")
                .destinationIp("192.168.0.1")
                .build();

        Alert savedAlert = Alert.builder()
                .id(2L)
                .title("Malware Detected")
                .description("Ransomware signature found")
                .severity(Severity.CRITICAL)
                .status(Status.OPEN)
                .sourceIp("10.10.10.10")
                .destinationIp("192.168.0.1")
                .createdAt(LocalDateTime.now())
                .build();

        when(alertRepository.save(any(Alert.class))).thenReturn(savedAlert);

        AlertDTO result = alertService.createAlert(inputDto);

        assertThat(result).isNotNull();
        assertThat(result.getId()).isEqualTo(2L);
        assertThat(result.getTitle()).isEqualTo("Malware Detected");
        assertThat(result.getStatus()).isEqualTo(Status.OPEN);

        ArgumentCaptor<Alert> alertCaptor = ArgumentCaptor.forClass(Alert.class);
        verify(alertRepository).save(alertCaptor.capture());
        assertThat(alertCaptor.getValue().getTitle()).isEqualTo("Malware Detected");
        assertThat(alertCaptor.getValue().getStatus()).isEqualTo(Status.OPEN);
    }

    @Test
    @DisplayName("createAlert - broadcasts CRITICAL alert via WebSocket")
    void createAlert_broadcastsCriticalAlertViaWebSocket() {
        AlertDTO inputDto = AlertDTO.builder()
                .title("Critical Alert")
                .severity(Severity.CRITICAL)
                .build();

        Alert savedAlert = Alert.builder()
                .id(3L).title("Critical Alert")
                .severity(Severity.CRITICAL).status(Status.OPEN)
                .createdAt(LocalDateTime.now()).build();

        when(alertRepository.save(any(Alert.class))).thenReturn(savedAlert);

        alertService.createAlert(inputDto);

        verify(messagingTemplate).convertAndSend(eq("/topic/alerts"), any(AlertDTO.class));
    }

    @Test
    @DisplayName("createAlert - does NOT broadcast LOW severity alert")
    void createAlert_doesNotBroadcastLowAlert() {
        AlertDTO inputDto = AlertDTO.builder()
                .title("Low Alert")
                .severity(Severity.LOW)
                .build();

        Alert savedAlert = Alert.builder()
                .id(4L).title("Low Alert")
                .severity(Severity.LOW).status(Status.OPEN)
                .createdAt(LocalDateTime.now()).build();

        when(alertRepository.save(any(Alert.class))).thenReturn(savedAlert);

        alertService.createAlert(inputDto);

        verify(messagingTemplate, never()).convertAndSend(anyString(), any(Object.class));
    }

    @Test
    @DisplayName("createAlert - assigns user when assignedToId provided")
    void createAlert_assignsUser_whenAssignedToIdProvided() {
        AlertDTO inputDto = AlertDTO.builder()
                .title("Assigned Alert")
                .severity(Severity.MEDIUM)
                .assignedToId(1L)
                .build();

        when(userRepository.findById(1L)).thenReturn(Optional.of(sampleUser));
        Alert savedAlert = Alert.builder()
                .id(5L).title("Assigned Alert").severity(Severity.MEDIUM)
                .status(Status.OPEN).assignedTo(sampleUser)
                .createdAt(LocalDateTime.now()).build();
        when(alertRepository.save(any(Alert.class))).thenReturn(savedAlert);

        AlertDTO result = alertService.createAlert(inputDto);

        assertThat(result.getAssignedToId()).isEqualTo(1L);
        assertThat(result.getAssignedToUsername()).isEqualTo("analyst1");
    }

    @Test
    @DisplayName("createAlert - throws ResourceNotFoundException when assignee not found")
    void createAlert_throwsException_whenAssigneeNotFound() {
        AlertDTO inputDto = AlertDTO.builder()
                .title("Alert")
                .severity(Severity.LOW)
                .assignedToId(999L)
                .build();

        when(userRepository.findById(999L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> alertService.createAlert(inputDto))
                .isInstanceOf(ResourceNotFoundException.class)
                .hasMessageContaining("User");
    }

    // ==================== UPDATE TESTS ====================

    @Test
    @DisplayName("updateAlertStatus - updates status correctly")
    void updateAlertStatus_updatesStatus() {
        when(alertRepository.findById(1L)).thenReturn(Optional.of(sampleAlert));
        Alert updatedAlert = Alert.builder()
                .id(1L).title("Suspicious SSH Login")
                .severity(Severity.HIGH).status(Status.RESOLVED)
                .createdAt(LocalDateTime.now()).updatedAt(LocalDateTime.now()).build();
        when(alertRepository.save(any(Alert.class))).thenReturn(updatedAlert);

        AlertDTO result = alertService.updateAlertStatus(1L, Status.RESOLVED);

        assertThat(result.getStatus()).isEqualTo(Status.RESOLVED);
        ArgumentCaptor<Alert> captor = ArgumentCaptor.forClass(Alert.class);
        verify(alertRepository).save(captor.capture());
        assertThat(captor.getValue().getStatus()).isEqualTo(Status.RESOLVED);
    }

    @Test
    @DisplayName("assignAlert - assigns user and sets IN_PROGRESS status")
    void assignAlert_assignsUserAndSetsInProgress() {
        when(alertRepository.findById(1L)).thenReturn(Optional.of(sampleAlert));
        when(userRepository.findById(1L)).thenReturn(Optional.of(sampleUser));

        Alert savedAlert = Alert.builder()
                .id(1L).title("Suspicious SSH Login")
                .severity(Severity.HIGH).status(Status.IN_PROGRESS)
                .assignedTo(sampleUser)
                .createdAt(LocalDateTime.now()).updatedAt(LocalDateTime.now()).build();
        when(alertRepository.save(any(Alert.class))).thenReturn(savedAlert);

        AlertDTO result = alertService.assignAlert(1L, 1L);

        assertThat(result.getStatus()).isEqualTo(Status.IN_PROGRESS);
        assertThat(result.getAssignedToUsername()).isEqualTo("analyst1");
    }

    // ==================== DELETE TESTS ====================

    @Test
    @DisplayName("deleteAlert - deletes alert successfully when exists")
    void deleteAlert_deletesSuccessfully_whenExists() {
        when(alertRepository.existsById(1L)).thenReturn(true);

        assertThatCode(() -> alertService.deleteAlert(1L)).doesNotThrowAnyException();
        verify(alertRepository).deleteById(1L);
    }

    @Test
    @DisplayName("deleteAlert - throws ResourceNotFoundException when not found")
    void deleteAlert_throwsException_whenNotFound() {
        when(alertRepository.existsById(999L)).thenReturn(false);

        assertThatThrownBy(() -> alertService.deleteAlert(999L))
                .isInstanceOf(ResourceNotFoundException.class)
                .hasMessageContaining("Alert");

        verify(alertRepository, never()).deleteById(any());
    }

    // ==================== STATISTICS TESTS ====================

    @Test
    @DisplayName("getAlertStatistics - returns statistics map with all expected keys")
    void getAlertStatistics_returnsCompleteStats() {
        when(alertRepository.count()).thenReturn(100L);
        when(alertRepository.countByStatus(Status.OPEN)).thenReturn(40L);
        when(alertRepository.countByStatus(Status.IN_PROGRESS)).thenReturn(20L);
        when(alertRepository.countByStatus(Status.RESOLVED)).thenReturn(30L);
        when(alertRepository.countBySeverity(Severity.CRITICAL)).thenReturn(5L);
        when(alertRepository.countBySeverity(Severity.HIGH)).thenReturn(15L);
        when(alertRepository.countBySeverity(Severity.MEDIUM)).thenReturn(50L);
        when(alertRepository.countBySeverity(Severity.LOW)).thenReturn(30L);
        when(alertRepository.countBySeveritySince(any(LocalDateTime.class))).thenReturn(List.of());

        var stats = alertService.getAlertStatistics();

        assertThat(stats).containsKeys("total", "open", "inProgress", "resolved",
                "critical", "high", "medium", "low", "last24hBySeverity");
        assertThat(stats.get("total")).isEqualTo(100L);
        assertThat(stats.get("open")).isEqualTo(40L);
        assertThat(stats.get("critical")).isEqualTo(5L);
    }
}

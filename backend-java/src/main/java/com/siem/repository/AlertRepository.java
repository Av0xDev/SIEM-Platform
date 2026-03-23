package com.siem.repository;

import com.siem.model.Alert;
import com.siem.model.Alert.Severity;
import com.siem.model.Alert.Status;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Repository
public interface AlertRepository extends JpaRepository<Alert, Long>, JpaSpecificationExecutor<Alert> {

    Page<Alert> findBySeverity(Severity severity, Pageable pageable);

    Page<Alert> findByStatus(Status status, Pageable pageable);

    Page<Alert> findBySeverityAndStatus(Severity severity, Status status, Pageable pageable);

    Page<Alert> findByAssignedToId(Long userId, Pageable pageable);

    List<Alert> findByCorrelationId(String correlationId);

    Page<Alert> findByCreatedAtBetween(LocalDateTime start, LocalDateTime end, Pageable pageable);

    Page<Alert> findBySourceIp(String sourceIp, Pageable pageable);

    @Query("SELECT a FROM Alert a WHERE a.status = 'OPEN' ORDER BY " +
           "CASE a.severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END, " +
           "a.createdAt ASC")
    List<Alert> findOpenAlertsByPriority(Pageable pageable);

    @Query("SELECT COUNT(a) FROM Alert a WHERE a.severity = :severity AND a.status != 'CLOSED'")
    long countActiveBySeverity(@Param("severity") Severity severity);

    @Query("SELECT a.severity as severity, COUNT(a) as count FROM Alert a " +
           "WHERE a.createdAt >= :since GROUP BY a.severity")
    List<Object[]> countBySeveritySince(@Param("since") LocalDateTime since);

    @Query("SELECT a.status as status, COUNT(a) as count FROM Alert a GROUP BY a.status")
    List<Object[]> countByStatus();

    @Query("SELECT a FROM Alert a WHERE a.falsePositive = false AND a.status = 'OPEN' " +
           "AND a.createdAt >= :since ORDER BY a.createdAt DESC")
    Page<Alert> findRecentOpenAlerts(@Param("since") LocalDateTime since, Pageable pageable);

    long countByStatus(Status status);

    long countBySeverity(Severity severity);
}

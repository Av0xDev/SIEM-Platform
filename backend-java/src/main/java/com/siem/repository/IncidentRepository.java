package com.siem.repository;

import com.siem.model.Incident;
import com.siem.model.Incident.Severity;
import com.siem.model.Incident.Status;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

@Repository
public interface IncidentRepository extends JpaRepository<Incident, Long>, JpaSpecificationExecutor<Incident> {

    Page<Incident> findBySeverity(Severity severity, Pageable pageable);

    Page<Incident> findByStatus(Status status, Pageable pageable);

    Page<Incident> findByAssignedToId(Long userId, Pageable pageable);

    Page<Incident> findByCreatedByIdAndStatus(Long userId, Status status, Pageable pageable);

    @Query("SELECT i FROM Incident i WHERE i.status NOT IN ('CLOSED', 'RECOVERED') " +
           "ORDER BY CASE i.severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END")
    List<Incident> findActiveIncidentsByPriority(Pageable pageable);

    @Query("SELECT COUNT(i) FROM Incident i WHERE i.status NOT IN ('CLOSED', 'RECOVERED')")
    long countActiveIncidents();

    @Query("SELECT i FROM Incident i WHERE i.createdAt >= :since ORDER BY i.createdAt DESC")
    Page<Incident> findRecentIncidents(@Param("since") LocalDateTime since, Pageable pageable);

    long countByStatus(Status status);
}

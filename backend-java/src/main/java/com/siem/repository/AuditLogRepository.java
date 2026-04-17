package com.siem.repository;

import com.siem.model.AuditLog;
import com.siem.model.AuditLog.Action;
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
public interface AuditLogRepository extends JpaRepository<AuditLog, Long>, JpaSpecificationExecutor<AuditLog> {

    Page<AuditLog> findByUserId(Long userId, Pageable pageable);

    Page<AuditLog> findByUsername(String username, Pageable pageable);

    Page<AuditLog> findByAction(Action action, Pageable pageable);

    Page<AuditLog> findByResourceType(String resourceType, Pageable pageable);

    Page<AuditLog> findByResourceTypeAndResourceId(String resourceType, String resourceId, Pageable pageable);

    Page<AuditLog> findByCreatedAtBetween(LocalDateTime start, LocalDateTime end, Pageable pageable);

    @Query("SELECT a FROM AuditLog a WHERE a.success = false AND a.createdAt >= :since ORDER BY a.createdAt DESC")
    List<AuditLog> findRecentFailures(@Param("since") LocalDateTime since);

    @Query("SELECT a FROM AuditLog a WHERE a.action = 'LOGIN_FAILED' AND a.ipAddress = :ip " +
           "AND a.createdAt >= :since")
    List<AuditLog> findFailedLoginsByIp(@Param("ip") String ip, @Param("since") LocalDateTime since);

    @Query("SELECT COUNT(a) FROM AuditLog a WHERE a.action = 'LOGIN_FAILED' AND a.username = :username " +
           "AND a.createdAt >= :since")
    long countFailedLoginsByUsername(@Param("username") String username, @Param("since") LocalDateTime since);
}

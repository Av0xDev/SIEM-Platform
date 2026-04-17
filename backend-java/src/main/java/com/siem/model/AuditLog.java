package com.siem.model;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import lombok.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;

@Entity
@Table(name = "audit_logs", indexes = {
        @Index(name = "idx_audit_log_user", columnList = "user_id"),
        @Index(name = "idx_audit_log_action", columnList = "action"),
        @Index(name = "idx_audit_log_resource", columnList = "resource_type"),
        @Index(name = "idx_audit_log_created_at", columnList = "created_at")
})
@EntityListeners(AuditingEntityListener.class)
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AuditLog {

    public enum Action {
        CREATE, READ, UPDATE, DELETE, LOGIN, LOGOUT, LOGIN_FAILED, EXPORT,
        ASSIGN, ESCALATE, RESOLVE, CLOSE
    }

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    private User user;

    @Column(name = "username", length = 50)
    private String username;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 30)
    private Action action;

    @NotBlank
    @Column(name = "resource_type", nullable = false, length = 50)
    private String resourceType;

    @Column(name = "resource_id", length = 100)
    private String resourceId;

    @Column(columnDefinition = "TEXT")
    private String details;

    @Column(name = "ip_address", length = 45)
    private String ipAddress;

    @Column(name = "user_agent", length = 255)
    private String userAgent;

    @Column(nullable = false)
    @Builder.Default
    private boolean success = true;

    @Column(name = "error_message", length = 500)
    private String errorMessage;

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;
}

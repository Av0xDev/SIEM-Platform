package com.siem.model;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;

@Entity
@Table(name = "threat_feeds", indexes = {
        @Index(name = "idx_threat_feed_indicator", columnList = "indicator"),
        @Index(name = "idx_threat_feed_type", columnList = "indicator_type"),
        @Index(name = "idx_threat_feed_active", columnList = "active"),
        @Index(name = "idx_threat_feed_confidence", columnList = "confidence_score")
})
@EntityListeners(AuditingEntityListener.class)
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ThreatFeed {

    public enum IndicatorType {
        IP_ADDRESS, DOMAIN, URL, FILE_HASH, EMAIL, CERTIFICATE
    }

    public enum ThreatType {
        MALWARE, PHISHING, C2, BOTNET, RANSOMWARE, APT, EXPLOIT, VULNERABILITY, OTHER
    }

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @NotBlank
    @Size(max = 500)
    @Column(nullable = false, length = 500)
    private String indicator;

    @Enumerated(EnumType.STRING)
    @Column(name = "indicator_type", nullable = false, length = 30)
    private IndicatorType indicatorType;

    @Enumerated(EnumType.STRING)
    @Column(name = "threat_type", length = 30)
    private ThreatType threatType;

    @Size(max = 100)
    @Column(length = 100)
    private String source;

    @Column(columnDefinition = "TEXT")
    private String description;

    @Column(name = "confidence_score")
    @Builder.Default
    private Integer confidenceScore = 50;

    @Column(name = "severity_score")
    @Builder.Default
    private Integer severityScore = 50;

    @Column(nullable = false)
    @Builder.Default
    private boolean active = true;

    @Column(name = "first_seen")
    private LocalDateTime firstSeen;

    @Column(name = "last_seen")
    private LocalDateTime lastSeen;

    @Column(name = "expiry_date")
    private LocalDateTime expiryDate;

    @Column(name = "tags", length = 500)
    private String tags;

    @Column(name = "raw_data", columnDefinition = "TEXT")
    private String rawData;

    @Column(name = "hit_count")
    @Builder.Default
    private Integer hitCount = 0;

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}

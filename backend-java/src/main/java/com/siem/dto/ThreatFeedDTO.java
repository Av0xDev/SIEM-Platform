package com.siem.dto;

import com.siem.model.ThreatFeed;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ThreatFeedDTO {

    private Long id;

    @NotBlank(message = "Indicator is required")
    private String indicator;

    @NotNull(message = "Indicator type is required")
    private ThreatFeed.IndicatorType indicatorType;

    private ThreatFeed.ThreatType threatType;
    private String source;
    private String description;

    @Min(0) @Max(100)
    @Builder.Default
    private Integer confidenceScore = 50;

    @Min(0) @Max(100)
    @Builder.Default
    private Integer severityScore = 50;

    private boolean active;
    private String tags;
    private LocalDateTime firstSeen;
    private LocalDateTime lastSeen;
    private LocalDateTime expiryDate;
    private Integer hitCount;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public static ThreatFeedDTO fromEntity(ThreatFeed tf) {
        return ThreatFeedDTO.builder()
                .id(tf.getId())
                .indicator(tf.getIndicator())
                .indicatorType(tf.getIndicatorType())
                .threatType(tf.getThreatType())
                .source(tf.getSource())
                .description(tf.getDescription())
                .confidenceScore(tf.getConfidenceScore())
                .severityScore(tf.getSeverityScore())
                .active(tf.isActive())
                .tags(tf.getTags())
                .firstSeen(tf.getFirstSeen())
                .lastSeen(tf.getLastSeen())
                .expiryDate(tf.getExpiryDate())
                .hitCount(tf.getHitCount())
                .createdAt(tf.getCreatedAt())
                .updatedAt(tf.getUpdatedAt())
                .build();
    }
}

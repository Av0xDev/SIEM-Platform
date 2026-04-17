package com.siem.controller;

import com.siem.dto.ThreatFeedDTO;
import com.siem.model.ThreatFeed.IndicatorType;
import com.siem.model.AuditLog.Action;
import com.siem.service.AuditService;
import com.siem.service.ThreatIntelService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api/threat-intel")
@RequiredArgsConstructor
@Tag(name = "Threat Intelligence", description = "Threat feed and indicator management endpoints")
public class ThreatIntelController {

    private final ThreatIntelService threatIntelService;
    private final AuditService auditService;

    @Operation(summary = "List threat feeds", description = "Retrieve paginated threat intelligence feeds")
    @GetMapping
    public ResponseEntity<Page<ThreatFeedDTO>> getFeeds(
            @Parameter(description = "Filter by indicator type") @RequestParam(required = false) IndicatorType type,
            @Parameter(description = "Active feeds only") @RequestParam(defaultValue = "false") boolean activeOnly,
            @Parameter(description = "Minimum confidence score (0-100)") @RequestParam(required = false) Integer minConfidence,
            @PageableDefault(size = 20) Pageable pageable) {

        Page<ThreatFeedDTO> feeds;
        if (minConfidence != null) {
            feeds = threatIntelService.getHighConfidenceFeeds(minConfidence, pageable);
        } else if (type != null) {
            feeds = threatIntelService.getFeedsByType(type, pageable);
        } else if (activeOnly) {
            feeds = threatIntelService.getActiveFeeds(pageable);
        } else {
            feeds = threatIntelService.getAllFeeds(pageable);
        }
        return ResponseEntity.ok(feeds);
    }

    @Operation(summary = "Get threat feed by ID")
    @GetMapping("/{id}")
    public ResponseEntity<ThreatFeedDTO> getFeed(@PathVariable Long id) {
        return ResponseEntity.ok(threatIntelService.getFeedById(id));
    }

    @Operation(summary = "Lookup indicator", description = "Check if a specific indicator exists in the threat feeds")
    @GetMapping("/lookup")
    public ResponseEntity<ThreatFeedDTO> lookup(
            @Parameter(description = "Indicator value to look up") @RequestParam String indicator,
            @Parameter(description = "Type of indicator") @RequestParam IndicatorType type) {

        Optional<ThreatFeedDTO> result = threatIntelService.lookupIndicator(indicator, type);
        return result.map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @Operation(summary = "Check if indicator is malicious",
               description = "Returns true if the indicator is active and has confidence >= 70")
    @GetMapping("/check")
    public ResponseEntity<Map<String, Object>> checkIndicator(
            @RequestParam String indicator,
            @RequestParam IndicatorType type) {

        boolean malicious = threatIntelService.isMalicious(indicator, type);
        return ResponseEntity.ok(Map.of(
                "indicator", indicator,
                "type", type,
                "malicious", malicious
        ));
    }

    @Operation(summary = "Get threat intel statistics")
    @GetMapping("/statistics")
    public ResponseEntity<Map<String, Object>> getStatistics() {
        return ResponseEntity.ok(Map.of(
                "activeFeeds", threatIntelService.getActiveFeedCount()
        ));
    }

    @Operation(summary = "Create threat feed entry")
    @PostMapping
    @PreAuthorize("hasAnyRole('ADMIN', 'ANALYST')")
    public ResponseEntity<ThreatFeedDTO> createFeed(
            @Valid @RequestBody ThreatFeedDTO dto,
            Authentication auth,
            HttpServletRequest request) {

        ThreatFeedDTO created = threatIntelService.createFeed(dto);
        auditService.log(auth.getName(), Action.CREATE, "THREAT_FEED",
                String.valueOf(created.getId()), "Feed created: " + created.getIndicator(),
                request.getRemoteAddr(), true);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }

    @Operation(summary = "Update threat feed entry")
    @PutMapping("/{id}")
    @PreAuthorize("hasAnyRole('ADMIN', 'ANALYST')")
    public ResponseEntity<ThreatFeedDTO> updateFeed(
            @PathVariable Long id,
            @Valid @RequestBody ThreatFeedDTO dto,
            Authentication auth,
            HttpServletRequest request) {

        ThreatFeedDTO updated = threatIntelService.updateFeed(id, dto);
        auditService.log(auth.getName(), Action.UPDATE, "THREAT_FEED",
                String.valueOf(id), "Feed updated", request.getRemoteAddr(), true);
        return ResponseEntity.ok(updated);
    }

    @Operation(summary = "Deactivate threat feed entry")
    @PatchMapping("/{id}/deactivate")
    @PreAuthorize("hasAnyRole('ADMIN', 'ANALYST')")
    public ResponseEntity<Void> deactivateFeed(
            @PathVariable Long id,
            Authentication auth,
            HttpServletRequest request) {

        threatIntelService.deactivateFeed(id);
        auditService.log(auth.getName(), Action.UPDATE, "THREAT_FEED",
                String.valueOf(id), "Feed deactivated", request.getRemoteAddr(), true);
        return ResponseEntity.noContent().build();
    }

    @Operation(summary = "Delete threat feed entry")
    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Void> deleteFeed(
            @PathVariable Long id,
            Authentication auth,
            HttpServletRequest request) {

        threatIntelService.deleteFeed(id);
        auditService.log(auth.getName(), Action.DELETE, "THREAT_FEED",
                String.valueOf(id), "Feed deleted", request.getRemoteAddr(), true);
        return ResponseEntity.noContent().build();
    }
}

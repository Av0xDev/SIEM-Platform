package com.siem.service;

import com.siem.dto.ThreatFeedDTO;
import com.siem.exception.DuplicateResourceException;
import com.siem.exception.ResourceNotFoundException;
import com.siem.model.ThreatFeed;
import com.siem.model.ThreatFeed.IndicatorType;
import com.siem.repository.ThreatFeedRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class ThreatIntelService {

    private final ThreatFeedRepository threatFeedRepository;

    public Page<ThreatFeedDTO> getAllFeeds(Pageable pageable) {
        return threatFeedRepository.findAll(pageable).map(ThreatFeedDTO::fromEntity);
    }

    public Page<ThreatFeedDTO> getActiveFeeds(Pageable pageable) {
        return threatFeedRepository.findByActiveTrue(pageable).map(ThreatFeedDTO::fromEntity);
    }

    public Page<ThreatFeedDTO> getFeedsByType(IndicatorType type, Pageable pageable) {
        return threatFeedRepository.findByIndicatorType(type, pageable).map(ThreatFeedDTO::fromEntity);
    }

    public Page<ThreatFeedDTO> getHighConfidenceFeeds(int minConfidence, Pageable pageable) {
        return threatFeedRepository.findHighConfidenceFeeds(minConfidence, pageable)
                .map(ThreatFeedDTO::fromEntity);
    }

    public ThreatFeedDTO getFeedById(Long id) {
        return threatFeedRepository.findById(id)
                .map(ThreatFeedDTO::fromEntity)
                .orElseThrow(() -> new ResourceNotFoundException("ThreatFeed", "id", id));
    }

    public Optional<ThreatFeedDTO> lookupIndicator(String indicator, IndicatorType type) {
        return threatFeedRepository.findByIndicatorAndIndicatorType(indicator, type)
                .filter(ThreatFeed::isActive)
                .map(feed -> {
                    threatFeedRepository.incrementHitCount(feed.getId(), LocalDateTime.now());
                    return ThreatFeedDTO.fromEntity(feed);
                });
    }

    public boolean isMalicious(String indicator, IndicatorType type) {
        return threatFeedRepository.findByIndicatorAndIndicatorType(indicator, type)
                .map(feed -> feed.isActive() && feed.getConfidenceScore() >= 70)
                .orElse(false);
    }

    @Transactional
    public ThreatFeedDTO createFeed(ThreatFeedDTO dto) {
        if (threatFeedRepository.existsByIndicatorAndIndicatorType(
                dto.getIndicator(), dto.getIndicatorType())) {
            throw new DuplicateResourceException(
                    "Threat indicator already exists: " + dto.getIndicator());
        }

        ThreatFeed feed = ThreatFeed.builder()
                .indicator(dto.getIndicator())
                .indicatorType(dto.getIndicatorType())
                .threatType(dto.getThreatType())
                .source(dto.getSource())
                .description(dto.getDescription())
                .confidenceScore(dto.getConfidenceScore())
                .severityScore(dto.getSeverityScore())
                .active(true)
                .tags(dto.getTags())
                .firstSeen(dto.getFirstSeen() != null ? dto.getFirstSeen() : LocalDateTime.now())
                .lastSeen(dto.getLastSeen())
                .expiryDate(dto.getExpiryDate())
                .rawData(null)
                .build();

        ThreatFeed saved = threatFeedRepository.save(feed);
        log.info("Threat feed created: id={}, indicator={}", saved.getId(), saved.getIndicator());
        return ThreatFeedDTO.fromEntity(saved);
    }

    @Transactional
    public ThreatFeedDTO updateFeed(Long id, ThreatFeedDTO dto) {
        ThreatFeed feed = threatFeedRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("ThreatFeed", "id", id));

        feed.setIndicator(dto.getIndicator());
        feed.setIndicatorType(dto.getIndicatorType());
        feed.setThreatType(dto.getThreatType());
        feed.setSource(dto.getSource());
        feed.setDescription(dto.getDescription());
        feed.setConfidenceScore(dto.getConfidenceScore());
        feed.setSeverityScore(dto.getSeverityScore());
        feed.setActive(dto.isActive());
        feed.setTags(dto.getTags());
        feed.setExpiryDate(dto.getExpiryDate());

        return ThreatFeedDTO.fromEntity(threatFeedRepository.save(feed));
    }

    @Transactional
    public void deleteFeed(Long id) {
        if (!threatFeedRepository.existsById(id)) {
            throw new ResourceNotFoundException("ThreatFeed", "id", id);
        }
        threatFeedRepository.deleteById(id);
        log.info("Threat feed {} deleted", id);
    }

    @Transactional
    public void deactivateFeed(Long id) {
        ThreatFeed feed = threatFeedRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("ThreatFeed", "id", id));
        feed.setActive(false);
        threatFeedRepository.save(feed);
    }

    /** Scheduled job: expire stale feeds every hour */
    @Scheduled(fixedDelay = 3_600_000)
    @Transactional
    public void expireStaleFeeds() {
        List<ThreatFeed> expired = threatFeedRepository.findExpiredFeeds(LocalDateTime.now());
        expired.forEach(feed -> feed.setActive(false));
        if (!expired.isEmpty()) {
            threatFeedRepository.saveAll(expired);
            log.info("Deactivated {} expired threat feeds", expired.size());
        }
    }

    public long getActiveFeedCount() {
        return threatFeedRepository.countByActiveTrue();
    }
}

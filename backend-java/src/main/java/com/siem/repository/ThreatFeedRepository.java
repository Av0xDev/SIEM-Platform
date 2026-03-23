package com.siem.repository;

import com.siem.model.ThreatFeed;
import com.siem.model.ThreatFeed.IndicatorType;
import com.siem.model.ThreatFeed.ThreatType;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface ThreatFeedRepository extends JpaRepository<ThreatFeed, Long>, JpaSpecificationExecutor<ThreatFeed> {

    Optional<ThreatFeed> findByIndicatorAndIndicatorType(String indicator, IndicatorType indicatorType);

    Page<ThreatFeed> findByActiveTrue(Pageable pageable);

    Page<ThreatFeed> findByIndicatorType(IndicatorType indicatorType, Pageable pageable);

    Page<ThreatFeed> findByThreatType(ThreatType threatType, Pageable pageable);

    List<ThreatFeed> findByActiveTrueAndIndicatorIn(List<String> indicators);

    @Query("SELECT t FROM ThreatFeed t WHERE t.active = true AND t.confidenceScore >= :minConfidence " +
           "ORDER BY t.confidenceScore DESC")
    Page<ThreatFeed> findHighConfidenceFeeds(@Param("minConfidence") int minConfidence, Pageable pageable);

    @Query("SELECT t FROM ThreatFeed t WHERE t.expiryDate IS NOT NULL AND t.expiryDate < :now AND t.active = true")
    List<ThreatFeed> findExpiredFeeds(@Param("now") LocalDateTime now);

    @Modifying
    @Query("UPDATE ThreatFeed t SET t.hitCount = t.hitCount + 1, t.lastSeen = :now WHERE t.id = :id")
    void incrementHitCount(@Param("id") Long id, @Param("now") LocalDateTime now);

    boolean existsByIndicatorAndIndicatorType(String indicator, IndicatorType indicatorType);

    long countByActiveTrue();
}

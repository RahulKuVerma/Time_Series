package com.hcltech.energyforecast.repository;

import com.hcltech.energyforecast.entity.ForecastRunEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface ForecastRunRepository extends JpaRepository<ForecastRunEntity, Long> {
    Optional<ForecastRunEntity> findByForecastUuid(String forecastUuid);
    List<ForecastRunEntity> findTop50ByOrderByCreatedAtDesc();
}

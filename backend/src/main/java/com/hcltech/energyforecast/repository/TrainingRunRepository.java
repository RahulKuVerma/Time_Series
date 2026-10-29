package com.hcltech.energyforecast.repository;

import com.hcltech.energyforecast.entity.TrainingRunEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface TrainingRunRepository extends JpaRepository<TrainingRunEntity, Long> {
    Optional<TrainingRunEntity> findByRunUuid(String runUuid);
    List<TrainingRunEntity> findTop50ByOrderByCreatedAtDesc();
}

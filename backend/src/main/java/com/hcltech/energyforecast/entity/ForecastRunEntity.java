package com.hcltech.energyforecast.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "forecast_runs")
public class ForecastRunEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String forecastUuid;

    @Column(nullable = false)
    private String modelName;

    @Column(nullable = false)
    private String buildingId;

    private Integer horizonHours;
    private String startTimestamp;
    private String endTimestamp;
    private String status;
    private LocalDateTime createdAt;

    @PrePersist
    public void prePersist() {
        if (this.createdAt == null) {
            this.createdAt = LocalDateTime.now();
        }
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getForecastUuid() { return forecastUuid; }
    public void setForecastUuid(String forecastUuid) { this.forecastUuid = forecastUuid; }
    public String getModelName() { return modelName; }
    public void setModelName(String modelName) { this.modelName = modelName; }
    public String getBuildingId() { return buildingId; }
    public void setBuildingId(String buildingId) { this.buildingId = buildingId; }
    public Integer getHorizonHours() { return horizonHours; }
    public void setHorizonHours(Integer horizonHours) { this.horizonHours = horizonHours; }
    public String getStartTimestamp() { return startTimestamp; }
    public void setStartTimestamp(String startTimestamp) { this.startTimestamp = startTimestamp; }
    public String getEndTimestamp() { return endTimestamp; }
    public void setEndTimestamp(String endTimestamp) { this.endTimestamp = endTimestamp; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}

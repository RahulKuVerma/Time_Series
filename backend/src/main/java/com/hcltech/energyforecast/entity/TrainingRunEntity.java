package com.hcltech.energyforecast.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "training_runs")
public class TrainingRunEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String runUuid;

    @Column(nullable = false)
    private String modelName;

    @Column(nullable = false)
    private String buildingId;

    private Integer trainSteps;
    private Integer testSteps;
    private Double mae;
    private Double rmse;
    private Double mape;
    private Double smape;
    private Double trainingTimeSec;
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
    public String getRunUuid() { return runUuid; }
    public void setRunUuid(String runUuid) { this.runUuid = runUuid; }
    public String getModelName() { return modelName; }
    public void setModelName(String modelName) { this.modelName = modelName; }
    public String getBuildingId() { return buildingId; }
    public void setBuildingId(String buildingId) { this.buildingId = buildingId; }
    public Integer getTrainSteps() { return trainSteps; }
    public void setTrainSteps(Integer trainSteps) { this.trainSteps = trainSteps; }
    public Integer getTestSteps() { return testSteps; }
    public void setTestSteps(Integer testSteps) { this.testSteps = testSteps; }
    public Double getMae() { return mae; }
    public void setMae(Double mae) { this.mae = mae; }
    public Double getRmse() { return rmse; }
    public void setRmse(Double rmse) { this.rmse = rmse; }
    public Double getMape() { return mape; }
    public void setMape(Double mape) { this.mape = mape; }
    public Double getSmape() { return smape; }
    public void setSmape(Double smape) { this.smape = smape; }
    public Double getTrainingTimeSec() { return trainingTimeSec; }
    public void setTrainingTimeSec(Double trainingTimeSec) { this.trainingTimeSec = trainingTimeSec; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}

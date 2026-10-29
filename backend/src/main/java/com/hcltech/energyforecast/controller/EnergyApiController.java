package com.hcltech.energyforecast.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.HashMap;
import java.util.Map;

@RestController
@Tag(name = "Energy Forecasting Gateway", description = "Enterprise REST endpoints for Time-Series ML pipeline")
public class EnergyApiController {

    private final WebClient mlServiceClient;

    public EnergyApiController(WebClient mlServiceClient) {
        this.mlServiceClient = mlServiceClient;
    }

    @GetMapping("/health")
    @Operation(summary = "System Health Status", description = "Returns gateway and downstream ML service health status")
    public ResponseEntity<Map<String, Object>> getHealth() {
        Map<String, Object> health = new HashMap<>();
        health.put("status", "UP");
        health.put("gateway", "Spring Boot 3.2.4 (Java 21)");
        try {
            Map<?, ?> mlHealth = mlServiceClient.get()
                    .uri("/health")
                    .retrieve()
                    .bodyToMono(Map.class)
                    .block();
            health.put("mlService", mlHealth);
        } catch (Exception e) {
            health.put("mlService", Map.of("status", "UNREACHABLE", "error", e.getMessage()));
        }
        return ResponseEntity.ok(health);
    }

    @GetMapping("/api/datasets/summary")
    @Operation(summary = "Dataset Summary", description = "Retrieve statistical metadata of the active dataset")
    public ResponseEntity<?> getDatasetSummary() {
        return proxyGet("/api/datasets/summary");
    }

    @GetMapping("/api/datasets/quality")
    @Operation(summary = "Dataset Quality Audit", description = "Returns validation issues, missing values, and anomalies")
    public ResponseEntity<?> getDatasetQuality() {
        return proxyGet("/api/datasets/quality");
    }

    @GetMapping("/api/eda/summary")
    @Operation(summary = "EDA Aggregations", description = "Returns diurnal, day-type, and correlation distributions")
    public ResponseEntity<?> getEdaSummary() {
        return proxyGet("/api/eda/summary");
    }

    @GetMapping("/api/models/metrics")
    @Operation(summary = "Model Benchmark Metrics", description = "Returns comparison metrics (MAE, RMSE, MAPE) across all models")
    public ResponseEntity<?> getModelMetrics() {
        return proxyGet("/api/models/metrics");
    }

    @PostMapping("/api/models/train")
    @Operation(summary = "Train Time-Series Model", description = "Triggers model training on selected building series")
    public ResponseEntity<?> trainModel(@RequestBody Map<String, Object> trainRequest) {
        return proxyPost("/api/models/train", trainRequest);
    }

    @PostMapping("/api/forecast")
    @Operation(summary = "Generate Multi-Step Forecast", description = "Forecasts future energy consumption up to 168 hours (7 days)")
    public ResponseEntity<?> generateForecast(@RequestBody Map<String, Object> forecastRequest) {
        return proxyPost("/api/forecast", forecastRequest);
    }

    @GetMapping("/api/forecast/history")
    @Operation(summary = "Forecast History", description = "Returns recorded forecast executions")
    public ResponseEntity<?> getForecastHistory() {
        return proxyGet("/api/forecast/history");
    }

    @GetMapping("/api/forecast/{forecastUuid}/download")
    @Operation(summary = "Download Forecast CSV", description = "Streams CSV of generated forecast run")
    public ResponseEntity<Resource> downloadForecastCsv(@PathVariable String forecastUuid) {
        Resource csvResource = mlServiceClient.get()
                .uri("/api/forecast/" + forecastUuid + "/download")
                .retrieve()
                .bodyToMono(Resource.class)
                .block();

        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=forecast_" + forecastUuid + ".csv")
                .contentType(MediaType.parseMediaType("text/csv"))
                .body(csvResource);
    }

    @GetMapping("/api/datasets/download/cleaned")
    @Operation(summary = "Download Cleaned Dataset", description = "Streams the canonical 6-column cleaned dataset.csv")
    public ResponseEntity<Resource> downloadCleanedDataset() {
        Resource csvResource = mlServiceClient.get()
                .uri("/api/datasets/download/cleaned")
                .retrieve()
                .bodyToMono(Resource.class)
                .block();

        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=dataset_cleaned.csv")
                .contentType(MediaType.parseMediaType("text/csv"))
                .body(csvResource);
    }

    private ResponseEntity<?> proxyGet(String uri) {
        try {
            Map<?, ?> response = mlServiceClient.get()
                    .uri(uri)
                    .retrieve()
                    .bodyToMono(Map.class)
                    .block();
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            return ResponseEntity.status(502).body(Map.of("error", "Error connecting to ML service: " + e.getMessage()));
        }
    }

    private ResponseEntity<?> proxyPost(String uri, Object body) {
        try {
            Map<?, ?> response = mlServiceClient.post()
                    .uri(uri)
                    .body(BodyInserters.fromValue(body))
                    .retrieve()
                    .bodyToMono(Map.class)
                    .block();
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            return ResponseEntity.status(502).body(Map.of("error", "Error executing ML service task: " + e.getMessage()));
        }
    }
}

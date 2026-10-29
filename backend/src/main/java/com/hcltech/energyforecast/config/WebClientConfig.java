package com.hcltech.energyforecast.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
public class WebClientConfig {

    @Value("${app.ml-service.base-url:http://localhost:8000}")
    private String mlServiceBaseUrl;

    @Bean
    public WebClient mlServiceWebClient() {
        return WebClient.builder()
                .baseUrl(mlServiceBaseUrl)
                .codecs(configurer -> configurer.defaultCodecs().maxInMemorySize(20 * 1024 * 1024))
                .build();
    }
}

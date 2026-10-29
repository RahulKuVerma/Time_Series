package com.hcltech.energyforecast.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI energyForecastOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("Energy Consumption Forecasting Gateway API")
                        .description("HCLTech Career Shaper Programme — III Year Industry Project (Project No. 33). " +
                                "Enterprise REST API connecting frontend dashboard to time-series forecasting models.")
                        .version("1.0.0")
                        .contact(new Contact()
                                .name("Rahul Kumar Verma")
                                .email("rahul.verma@example.com"))
                        .license(new License().name("Apache 2.0").url("https://www.apache.org/licenses/LICENSE-2.0")));
    }
}

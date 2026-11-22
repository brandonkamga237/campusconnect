package com.groupetp1.student_service.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;

/** Swagger UI : http://localhost:8083/swagger-ui.html (bouton « Authorize » pour coller le JWT). */
@Configuration
public class OpenApiConfig {

	@Bean
	OpenAPI studentServiceOpenApi() {
		return new OpenAPI()
				.info(new Info()
						.title("CampusConnect student-service")
						.version("1.0.0")
						.description("Référentiel académique : facultés, départements, filières, cycles et niveaux. "
								+ "Lecture : tout utilisateur connecté. Écriture : rôle ADMIN. "
								+ "Obtenir un JWT avec POST /api/auth/login sur auth-service."))
				.components(new Components().addSecuritySchemes("bearer", new SecurityScheme()
						.type(SecurityScheme.Type.HTTP).scheme("bearer").bearerFormat("JWT")))
				.addSecurityItem(new SecurityRequirement().addList("bearer"));
	}
}

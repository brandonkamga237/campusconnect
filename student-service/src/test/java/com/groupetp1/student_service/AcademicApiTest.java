package com.groupetp1.student_service;

import static org.hamcrest.Matchers.contains;
import static org.hamcrest.Matchers.hasSize;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.jwt;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Date;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockHttpServletRequestBuilder;
import org.springframework.test.web.servlet.request.RequestPostProcessor;

import com.jayway.jsonpath.JsonPath;
import com.nimbusds.jose.JWSAlgorithm;
import com.nimbusds.jose.JWSHeader;
import com.nimbusds.jose.crypto.MACSigner;
import com.nimbusds.jwt.JWTClaimsSet;
import com.nimbusds.jwt.SignedJWT;

@Import(TestcontainersConfiguration.class)
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class AcademicApiTest {

	private static final AtomicInteger SEQ = new AtomicInteger();
	private static final String LICENCE = "00000000-0000-0000-0000-000000000001";

	@Autowired
	MockMvc mvc;

	@Value("${jwt.secret}")
	String secret;

	// --- utilitaires --------------------------------------------------------------------------

	static RequestPostProcessor admin() {
		return jwt().authorities(new SimpleGrantedAuthority("ROLE_ADMIN"));
	}

	static RequestPostProcessor student() {
		return jwt().authorities(new SimpleGrantedAuthority("ROLE_STUDENT"));
	}

	static String unique(String prefix) {
		return prefix + SEQ.incrementAndGet();
	}

	static MockHttpServletRequestBuilder json(MockHttpServletRequestBuilder builder, String body) {
		return builder.contentType(MediaType.APPLICATION_JSON).content(body);
	}

	String createFaculty(String code) throws Exception {
		String body = mvc.perform(json(post("/api/faculties"), """
				{"code":"%s","name":"Faculté %s"}""".formatted(code, code)).with(admin()))
				.andExpect(status().isCreated()).andReturn().getResponse().getContentAsString();
		return JsonPath.read(body, "$.id");
	}

	String createDepartment(String facultyId, String code) throws Exception {
		String body = mvc.perform(json(post("/api/departments"), """
				{"facultyId":"%s","code":"%s","name":"Département %s"}""".formatted(facultyId, code, code))
				.with(admin())).andExpect(status().isCreated()).andReturn().getResponse().getContentAsString();
		return JsonPath.read(body, "$.id");
	}

	String createField(String departmentId, String code) throws Exception {
		String body = mvc.perform(json(post("/api/fields"), """
				{"departmentId":"%s","code":"%s","name":"Filière %s"}""".formatted(departmentId, code, code))
				.with(admin())).andExpect(status().isCreated()).andReturn().getResponse().getContentAsString();
		return JsonPath.read(body, "$.id");
	}

	String signedToken(String issuer, List<String> roles) throws Exception {
		JWTClaimsSet claims = new JWTClaimsSet.Builder().issuer(issuer).subject("user-1").claim("roles", roles)
				.issueTime(new Date()).expirationTime(Date.from(Instant.now().plusSeconds(300))).build();
		SignedJWT token = new SignedJWT(new JWSHeader(JWSAlgorithm.HS256), claims);
		token.sign(new MACSigner(secret.getBytes(StandardCharsets.UTF_8)));
		return token.serialize();
	}

	// --- sécurité -----------------------------------------------------------------------------

	@Test
	void requiresAToken() throws Exception {
		mvc.perform(get("/api/faculties")).andExpect(status().isUnauthorized())
				.andExpect(jsonPath("$.code").value("TOKEN_MISSING"));
	}

	@Test
	void acceptsRealAuthServiceTokensAndChecksRoles() throws Exception {
		String studentToken = signedToken("campusconnect-auth", List.of("STUDENT"));
		mvc.perform(get("/api/faculties").header("Authorization", "Bearer " + studentToken))
				.andExpect(status().isOk());
		mvc.perform(json(post("/api/faculties"), "{\"code\":\"X1\",\"name\":\"X\"}")
				.header("Authorization", "Bearer " + studentToken))
				.andExpect(status().isForbidden()).andExpect(jsonPath("$.code").value("FORBIDDEN"));

		String adminToken = signedToken("campusconnect-auth", List.of("ADMIN"));
		mvc.perform(json(post("/api/faculties"), "{\"code\":\"%s\",\"name\":\"X\"}".formatted(unique("TOK")))
				.header("Authorization", "Bearer " + adminToken)).andExpect(status().isCreated());

		String foreign = signedToken("someone-else", List.of("ADMIN"));
		mvc.perform(get("/api/faculties").header("Authorization", "Bearer " + foreign))
				.andExpect(status().isUnauthorized()).andExpect(jsonPath("$.code").value("TOKEN_INVALID"));
	}

	@Test
	void swaggerIsPublic() throws Exception {
		mvc.perform(get("/v3/api-docs")).andExpect(status().isOk())
				.andExpect(jsonPath("$.paths['/api/faculties']").exists())
				.andExpect(jsonPath("$.components.securitySchemes.bearer.scheme").value("bearer"));
		mvc.perform(get("/swagger-ui/index.html")).andExpect(status().isOk());
	}

	// --- facultés -----------------------------------------------------------------------------

	@Test
	void facultyLifecycle() throws Exception {
		String code = unique("sci");
		String body = mvc.perform(json(post("/api/faculties"), """
				{"code":"%s","name":"  Faculté des sciences ","description":"Maths, physique"}""".formatted(code))
				.with(admin()))
				.andExpect(status().isCreated())
				.andExpect(header().exists("Location"))
				.andExpect(jsonPath("$.code").value(code.toUpperCase()))
				.andExpect(jsonPath("$.name").value("Faculté des sciences"))
				.andExpect(jsonPath("$.status").value("ACTIVE"))
				.andExpect(jsonPath("$.createdAt").exists())
				.andReturn().getResponse().getContentAsString();
		String id = JsonPath.read(body, "$.id");

		mvc.perform(json(post("/api/faculties"), "{\"code\":\"%s\",\"name\":\"Doublon\"}".formatted(code))
				.with(admin())).andExpect(status().isConflict()).andExpect(jsonPath("$.code").value("CODE_TAKEN"));

		mvc.perform(get("/api/faculties/" + id).with(student())).andExpect(status().isOk())
				.andExpect(jsonPath("$.description").value("Maths, physique"));

		mvc.perform(json(put("/api/faculties/" + id), "{\"code\":\"%s\",\"name\":\"Sciences\"}".formatted(code))
				.with(admin())).andExpect(status().isOk()).andExpect(jsonPath("$.name").value("Sciences"))
				.andExpect(jsonPath("$.description").doesNotExist());

		mvc.perform(json(patch("/api/faculties/" + id + "/status"), "{\"status\":\"INACTIVE\"}").with(admin()))
				.andExpect(status().isOk()).andExpect(jsonPath("$.status").value("INACTIVE"));

		mvc.perform(get("/api/faculties").param("q", code).param("status", "INACTIVE").with(student()))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$.content", hasSize(1)))
				.andExpect(jsonPath("$.page.totalElements").value(1))
				.andExpect(jsonPath("$.page.size").value(20));

		mvc.perform(delete("/api/faculties/" + id).with(admin())).andExpect(status().isNoContent());
		mvc.perform(get("/api/faculties/" + id).with(admin())).andExpect(status().isNotFound())
				.andExpect(jsonPath("$.code").value("FACULTY_NOT_FOUND"));
	}

	@Test
	void validationAndBadParameters() throws Exception {
		mvc.perform(json(post("/api/faculties"), "{\"code\":\"bad code!\",\"name\":\"\"}").with(admin()))
				.andExpect(status().isBadRequest())
				.andExpect(header().string("Content-Type", "application/problem+json"))
				.andExpect(jsonPath("$.code").value("VALIDATION_FAILED"))
				.andExpect(jsonPath("$.errors", hasSize(2)));

		mvc.perform(get("/api/faculties/not-a-uuid").with(admin())).andExpect(status().isBadRequest())
				.andExpect(jsonPath("$.code").value("INVALID_PARAMETER"));
		mvc.perform(get("/api/faculties").param("sort", "password").with(admin()))
				.andExpect(status().isBadRequest()).andExpect(jsonPath("$.code").value("INVALID_SORT"));
	}

	// --- départements et filières -------------------------------------------------------------

	@Test
	void hierarchyRules() throws Exception {
		String facultyId = createFaculty(unique("FAC"));
		String departmentId = createDepartment(facultyId, unique("DEP"));
		String fieldCode = unique("GL");
		String fieldId = createField(departmentId, fieldCode);

		mvc.perform(get("/api/fields/" + fieldId).with(student())).andExpect(status().isOk())
				.andExpect(jsonPath("$.department.id").value(departmentId))
				.andExpect(jsonPath("$.faculty.id").value(facultyId));
		mvc.perform(get("/api/fields").param("facultyId", facultyId).with(student()))
				.andExpect(jsonPath("$.content[*].code", contains(fieldCode)));
		mvc.perform(get("/api/departments").param("facultyId", facultyId).with(student()))
				.andExpect(jsonPath("$.content", hasSize(1)));

		// suppression refusée tant qu'il y a des enfants
		mvc.perform(delete("/api/faculties/" + facultyId).with(admin())).andExpect(status().isConflict())
				.andExpect(jsonPath("$.code").value("RESOURCE_IN_USE"));
		mvc.perform(delete("/api/departments/" + departmentId).with(admin())).andExpect(status().isConflict());

		// pas de nouvel enfant sous un parent inactif
		mvc.perform(json(patch("/api/faculties/" + facultyId + "/status"), "{\"status\":\"INACTIVE\"}").with(admin()))
				.andExpect(status().isOk());
		mvc.perform(json(post("/api/departments"), """
				{"facultyId":"%s","code":"%s","name":"X"}""".formatted(facultyId, unique("DEP"))).with(admin()))
				.andExpect(status().isConflict()).andExpect(jsonPath("$.code").value("PARENT_INACTIVE"));

		mvc.perform(json(post("/api/departments"), """
				{"facultyId":"00000000-0000-0000-0000-00000000dead","code":"%s","name":"X"}""".formatted(unique("DEP")))
				.with(admin())).andExpect(status().isNotFound()).andExpect(jsonPath("$.code").value("FACULTY_NOT_FOUND"));

		// suppression de bas en haut
		mvc.perform(delete("/api/fields/" + fieldId).with(admin())).andExpect(status().isNoContent());
		mvc.perform(delete("/api/departments/" + departmentId).with(admin())).andExpect(status().isNoContent());
		mvc.perform(delete("/api/faculties/" + facultyId).with(admin())).andExpect(status().isNoContent());
	}

	@Test
	void moveDepartmentToAnotherFaculty() throws Exception {
		String from = createFaculty(unique("FAC"));
		String to = createFaculty(unique("FAC"));
		String code = unique("DEP");
		String departmentId = createDepartment(from, code);
		mvc.perform(json(put("/api/departments/" + departmentId), """
				{"facultyId":"%s","code":"%s","name":"Déplacé"}""".formatted(to, code)).with(admin()))
				.andExpect(status().isOk()).andExpect(jsonPath("$.faculty.id").value(to));
	}

	// --- cycles et niveaux --------------------------------------------------------------------

	@Test
	void lmdReferenceDataIsSeeded() throws Exception {
		mvc.perform(get("/api/academic-cycles").with(student())).andExpect(status().isOk())
				.andExpect(jsonPath("$[*].code", org.hamcrest.Matchers.hasItems("LICENCE", "MASTER", "DOCTORAT")));
		mvc.perform(get("/api/academic-cycles/" + LICENCE + "/levels").with(student()))
				.andExpect(jsonPath("$[*].code", contains("L1", "L2", "L3")))
				.andExpect(jsonPath("$[0].academicCycle.code").value("LICENCE"));
	}

	@Test
	void studyLevelRules() throws Exception {
		String cycleCode = unique("BTS");
		String body = mvc.perform(json(post("/api/academic-cycles"), """
				{"code":"%s","name":"Brevet de technicien supérieur"}""".formatted(cycleCode)).with(admin()))
				.andExpect(status().isCreated()).andReturn().getResponse().getContentAsString();
		String cycleId = JsonPath.read(body, "$.id");

		String level = """
				{"academicCycleId":"%s","code":"%s","name":"%s","position":%d}""";
		String b1 = unique("B");
		body = mvc.perform(json(post("/api/study-levels"), level.formatted(cycleId, b1, "Année 1", 1)).with(admin()))
				.andExpect(status().isCreated()).andReturn().getResponse().getContentAsString();
		String levelId = JsonPath.read(body, "$.id");

		mvc.perform(json(post("/api/study-levels"), level.formatted(cycleId, unique("B"), "Bis", 1)).with(admin()))
				.andExpect(status().isConflict()).andExpect(jsonPath("$.code").value("POSITION_TAKEN"));
		mvc.perform(json(post("/api/study-levels"), level.formatted(cycleId, "L1", "Doublon", 2)).with(admin()))
				.andExpect(status().isConflict()).andExpect(jsonPath("$.code").value("CODE_TAKEN"));
		mvc.perform(json(post("/api/study-levels"), level.formatted(cycleId, unique("B"), "Zéro", 0)).with(admin()))
				.andExpect(status().isBadRequest());

		mvc.perform(json(put("/api/study-levels/" + levelId), level.formatted(cycleId, b1, "Première année", 2))
				.with(admin())).andExpect(status().isOk()).andExpect(jsonPath("$.position").value(2));

		// cycle non supprimable tant qu'il a des niveaux
		mvc.perform(delete("/api/academic-cycles/" + cycleId).with(admin())).andExpect(status().isConflict());
		mvc.perform(delete("/api/study-levels/" + levelId).with(admin())).andExpect(status().isNoContent());
		mvc.perform(delete("/api/academic-cycles/" + cycleId).with(admin())).andExpect(status().isNoContent());
	}

	// --- cycles d'une filière -----------------------------------------------------------------

	@Test
	void fieldCycles() throws Exception {
		String fieldId = createField(createDepartment(createFaculty(unique("FAC")), unique("DEP")), unique("FLD"));
		String cycle = "{\"academicCycleId\":\"%s\"}";

		mvc.perform(json(post("/api/fields/" + fieldId + "/cycles"), cycle.formatted(LICENCE)).with(admin()))
				.andExpect(status().isCreated()).andExpect(jsonPath("$.academicCycle.code").value("LICENCE"))
				.andExpect(jsonPath("$.status").value("ACTIVE"));
		mvc.perform(json(post("/api/fields/" + fieldId + "/cycles"), cycle.formatted(LICENCE)).with(admin()))
				.andExpect(status().isConflict()).andExpect(jsonPath("$.code").value("FIELD_CYCLE_EXISTS"));
		mvc.perform(get("/api/fields/" + fieldId + "/cycles").with(student()))
				.andExpect(jsonPath("$", hasSize(1)));

		mvc.perform(json(patch("/api/fields/" + fieldId + "/cycles/" + LICENCE + "/status"), "{\"status\":\"INACTIVE\"}")
				.with(admin())).andExpect(status().isOk()).andExpect(jsonPath("$.status").value("INACTIVE"));

		// un cycle proposé par une filière ne peut pas être supprimé
		mvc.perform(delete("/api/academic-cycles/" + LICENCE).with(admin())).andExpect(status().isConflict());

		// un cycle inactif ne peut pas être rattaché
		String body = mvc.perform(json(post("/api/academic-cycles"), "{\"code\":\"%s\",\"name\":\"Vieux\"}"
				.formatted(unique("OLD"))).with(admin())).andReturn().getResponse().getContentAsString();
		String oldCycle = JsonPath.read(body, "$.id");
		mvc.perform(json(patch("/api/academic-cycles/" + oldCycle + "/status"), "{\"status\":\"INACTIVE\"}").with(admin()));
		mvc.perform(json(post("/api/fields/" + fieldId + "/cycles"), cycle.formatted(oldCycle)).with(admin()))
				.andExpect(status().isConflict()).andExpect(jsonPath("$.code").value("PARENT_INACTIVE"));

		mvc.perform(delete("/api/fields/" + fieldId + "/cycles/" + LICENCE).with(admin()))
				.andExpect(status().isNoContent());
		mvc.perform(delete("/api/fields/" + fieldId + "/cycles/" + LICENCE).with(admin()))
				.andExpect(status().isNotFound()).andExpect(jsonPath("$.code").value("FIELD_CYCLE_NOT_FOUND"));
	}

	@Test
	void deletingAFieldRemovesItsCycles() throws Exception {
		String fieldId = createField(createDepartment(createFaculty(unique("FAC")), unique("DEP")), unique("FLD"));
		mvc.perform(json(post("/api/fields/" + fieldId + "/cycles"), "{\"academicCycleId\":\"%s\"}".formatted(LICENCE))
				.with(admin())).andExpect(status().isCreated());
		mvc.perform(delete("/api/fields/" + fieldId).with(admin())).andExpect(status().isNoContent());
	}
}

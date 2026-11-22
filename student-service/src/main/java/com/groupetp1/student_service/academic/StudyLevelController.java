package com.groupetp1.student_service.academic;

import java.net.URI;
import java.util.List;
import java.util.UUID;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.groupetp1.student_service.academic.AcademicDtos.StudyLevelRequest;
import com.groupetp1.student_service.academic.AcademicDtos.StudyLevelResponse;

import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

@Tag(name = "Niveaux d'études")
@RestController
@RequestMapping("/api/study-levels")
@RequiredArgsConstructor
public class StudyLevelController {

	private final AcademicCycleService service;

	@GetMapping
	public List<StudyLevelResponse> list(@RequestParam(required = false) UUID academicCycleId) {
		return service.listLevels(academicCycleId);
	}

	@GetMapping("/{id}")
	public StudyLevelResponse get(@PathVariable UUID id) {
		return service.getLevel(id);
	}

	@PostMapping
	public ResponseEntity<StudyLevelResponse> create(@Valid @RequestBody StudyLevelRequest request) {
		StudyLevelResponse created = service.createLevel(request);
		return ResponseEntity.created(URI.create("/api/study-levels/" + created.id())).body(created);
	}

	@PutMapping("/{id}")
	public StudyLevelResponse update(@PathVariable UUID id, @Valid @RequestBody StudyLevelRequest request) {
		return service.updateLevel(id, request);
	}

	@DeleteMapping("/{id}")
	@ResponseStatus(HttpStatus.NO_CONTENT)
	public void delete(@PathVariable UUID id) {
		service.deleteLevel(id);
	}
}

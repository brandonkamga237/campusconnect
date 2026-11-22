package com.groupetp1.student_service.academic;

import java.net.URI;
import java.util.List;
import java.util.UUID;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.groupetp1.student_service.academic.AcademicDtos.AcademicCycleRequest;
import com.groupetp1.student_service.academic.AcademicDtos.AcademicCycleResponse;
import com.groupetp1.student_service.academic.AcademicDtos.StudyLevelResponse;
import com.groupetp1.student_service.common.RecordStatus;
import com.groupetp1.student_service.common.StatusRequest;

import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

@Tag(name = "Cycles")
@RestController
@RequestMapping("/api/academic-cycles")
@RequiredArgsConstructor
public class AcademicCycleController {

	private final AcademicCycleService service;

	@GetMapping
	public List<AcademicCycleResponse> list(@RequestParam(required = false) RecordStatus status) {
		return service.list(status);
	}

	@GetMapping("/{id}")
	public AcademicCycleResponse get(@PathVariable UUID id) {
		return service.get(id);
	}

	@GetMapping("/{id}/levels")
	public List<StudyLevelResponse> levels(@PathVariable UUID id) {
		return service.listLevels(id);
	}

	@PostMapping
	public ResponseEntity<AcademicCycleResponse> create(@Valid @RequestBody AcademicCycleRequest request) {
		AcademicCycleResponse created = service.create(request);
		return ResponseEntity.created(URI.create("/api/academic-cycles/" + created.id())).body(created);
	}

	@PutMapping("/{id}")
	public AcademicCycleResponse update(@PathVariable UUID id, @Valid @RequestBody AcademicCycleRequest request) {
		return service.update(id, request);
	}

	@PatchMapping("/{id}/status")
	public AcademicCycleResponse changeStatus(@PathVariable UUID id, @Valid @RequestBody StatusRequest request) {
		return service.changeStatus(id, request.status());
	}

	@DeleteMapping("/{id}")
	@ResponseStatus(HttpStatus.NO_CONTENT)
	public void delete(@PathVariable UUID id) {
		service.delete(id);
	}
}

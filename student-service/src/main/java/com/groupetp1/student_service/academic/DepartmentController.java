package com.groupetp1.student_service.academic;

import java.net.URI;
import java.util.UUID;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.web.PageableDefault;
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

import com.groupetp1.student_service.academic.AcademicDtos.DepartmentRequest;
import com.groupetp1.student_service.academic.AcademicDtos.DepartmentResponse;
import com.groupetp1.student_service.common.RecordStatus;
import com.groupetp1.student_service.common.StatusRequest;

import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

@Tag(name = "Départements")
@RestController
@RequestMapping("/api/departments")
@RequiredArgsConstructor
public class DepartmentController {

	private final DepartmentService service;

	@GetMapping
	public Page<DepartmentResponse> list(@RequestParam(required = false) UUID facultyId,
			@RequestParam(required = false) RecordStatus status,
			@RequestParam(required = false) String q,
			@PageableDefault(size = 20, sort = "name", direction = Sort.Direction.ASC) Pageable pageable) {
		return service.list(facultyId, status, q, pageable);
	}

	@GetMapping("/{id}")
	public DepartmentResponse get(@PathVariable UUID id) {
		return service.get(id);
	}

	@PostMapping
	public ResponseEntity<DepartmentResponse> create(@Valid @RequestBody DepartmentRequest request) {
		DepartmentResponse created = service.create(request);
		return ResponseEntity.created(URI.create("/api/departments/" + created.id())).body(created);
	}

	@PutMapping("/{id}")
	public DepartmentResponse update(@PathVariable UUID id, @Valid @RequestBody DepartmentRequest request) {
		return service.update(id, request);
	}

	@PatchMapping("/{id}/status")
	public DepartmentResponse changeStatus(@PathVariable UUID id, @Valid @RequestBody StatusRequest request) {
		return service.changeStatus(id, request.status());
	}

	@DeleteMapping("/{id}")
	@ResponseStatus(HttpStatus.NO_CONTENT)
	public void delete(@PathVariable UUID id) {
		service.delete(id);
	}
}

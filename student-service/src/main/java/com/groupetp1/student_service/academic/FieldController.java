package com.groupetp1.student_service.academic;

import java.net.URI;
import java.util.List;
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

import com.groupetp1.student_service.academic.AcademicDtos.FieldCycleRequest;
import com.groupetp1.student_service.academic.AcademicDtos.FieldCycleResponse;
import com.groupetp1.student_service.academic.AcademicDtos.FieldRequest;
import com.groupetp1.student_service.academic.AcademicDtos.FieldResponse;
import com.groupetp1.student_service.common.RecordStatus;
import com.groupetp1.student_service.common.StatusRequest;

import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

/** Filières et cycles qu'elles proposent. */
@Tag(name = "Filières")
@RestController
@RequestMapping("/api/fields")
@RequiredArgsConstructor
public class FieldController {

	private final FieldService service;

	@GetMapping
	public Page<FieldResponse> list(@RequestParam(required = false) UUID departmentId,
			@RequestParam(required = false) UUID facultyId,
			@RequestParam(required = false) RecordStatus status,
			@RequestParam(required = false) String q,
			@PageableDefault(size = 20, sort = "name", direction = Sort.Direction.ASC) Pageable pageable) {
		return service.list(departmentId, facultyId, status, q, pageable);
	}

	@GetMapping("/{id}")
	public FieldResponse get(@PathVariable UUID id) {
		return service.get(id);
	}

	@PostMapping
	public ResponseEntity<FieldResponse> create(@Valid @RequestBody FieldRequest request) {
		FieldResponse created = service.create(request);
		return ResponseEntity.created(URI.create("/api/fields/" + created.id())).body(created);
	}

	@PutMapping("/{id}")
	public FieldResponse update(@PathVariable UUID id, @Valid @RequestBody FieldRequest request) {
		return service.update(id, request);
	}

	@PatchMapping("/{id}/status")
	public FieldResponse changeStatus(@PathVariable UUID id, @Valid @RequestBody StatusRequest request) {
		return service.changeStatus(id, request.status());
	}

	@DeleteMapping("/{id}")
	@ResponseStatus(HttpStatus.NO_CONTENT)
	public void delete(@PathVariable UUID id) {
		service.delete(id);
	}

	// --- /api/fields/{id}/cycles -------------------------------------------------------------

	@GetMapping("/{id}/cycles")
	public List<FieldCycleResponse> listCycles(@PathVariable UUID id) {
		return service.listCycles(id);
	}

	@PostMapping("/{id}/cycles")
	@ResponseStatus(HttpStatus.CREATED)
	public FieldCycleResponse addCycle(@PathVariable UUID id, @Valid @RequestBody FieldCycleRequest request) {
		return service.addCycle(id, request.academicCycleId());
	}

	@PatchMapping("/{id}/cycles/{academicCycleId}/status")
	public FieldCycleResponse changeCycleStatus(@PathVariable UUID id, @PathVariable UUID academicCycleId,
			@Valid @RequestBody StatusRequest request) {
		return service.changeCycleStatus(id, academicCycleId, request.status());
	}

	@DeleteMapping("/{id}/cycles/{academicCycleId}")
	@ResponseStatus(HttpStatus.NO_CONTENT)
	public void removeCycle(@PathVariable UUID id, @PathVariable UUID academicCycleId) {
		service.removeCycle(id, academicCycleId);
	}
}

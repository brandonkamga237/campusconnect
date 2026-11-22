package com.groupetp1.student_service.academic;

import java.util.List;
import java.util.UUID;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.groupetp1.student_service.academic.AcademicDtos.FieldCycleResponse;
import com.groupetp1.student_service.academic.AcademicDtos.FieldRequest;
import com.groupetp1.student_service.academic.AcademicDtos.FieldResponse;
import com.groupetp1.student_service.common.ApiException;
import com.groupetp1.student_service.common.Codes;
import com.groupetp1.student_service.common.RecordStatus;
import com.groupetp1.student_service.common.Specs;

import lombok.RequiredArgsConstructor;

/** Filières et cycles qu'elles proposent. */
@Service
@RequiredArgsConstructor
@Transactional
public class FieldService {

	private final FieldRepository fields;
	private final FieldCycleRepository fieldCycles;
	private final DepartmentService departmentService;
	private final AcademicCycleService cycleService;

	@Transactional(readOnly = true)
	public Page<FieldResponse> list(UUID departmentId, UUID facultyId, RecordStatus status, String q,
			Pageable pageable) {
		return fields.findAll(Specs.<Field>catalog(status, q, (root, cb, predicates) -> {
			if (departmentId != null) {
				predicates.add(cb.equal(root.get("department").get("id"), departmentId));
			}
			if (facultyId != null) {
				predicates.add(cb.equal(root.get("department").get("faculty").get("id"), facultyId));
			}
		}), pageable).map(FieldResponse::of);
	}

	@Transactional(readOnly = true)
	public FieldResponse get(UUID id) {
		return FieldResponse.of(find(id));
	}

	public FieldResponse create(FieldRequest request) {
		ensureCodeFree(Codes.normalize(request.code()));
		Field field = new Field();
		field.setDepartment(activeDepartment(request.departmentId()));
		request.applyTo(field);
		return FieldResponse.of(fields.saveAndFlush(field));
	}

	public FieldResponse update(UUID id, FieldRequest request) {
		Field field = find(id);
		String code = Codes.normalize(request.code());
		if (!code.equals(field.getCode())) {
			ensureCodeFree(code);
		}
		if (!field.getDepartment().getId().equals(request.departmentId())) {
			field.setDepartment(activeDepartment(request.departmentId()));
		}
		request.applyTo(field);
		return FieldResponse.of(fields.saveAndFlush(field));
	}

	public FieldResponse changeStatus(UUID id, RecordStatus status) {
		Field field = find(id);
		field.setStatus(status);
		return FieldResponse.of(fields.saveAndFlush(field));
	}

	/** Supprime aussi les cycles rattachés à la filière (ON DELETE CASCADE). */
	public void delete(UUID id) {
		fields.delete(find(id));
	}

	// --- cycles proposés par la filière -----------------------------------------------------

	@Transactional(readOnly = true)
	public List<FieldCycleResponse> listCycles(UUID fieldId) {
		find(fieldId);
		return fieldCycles.findByFieldIdOrderByAcademicCycleCode(fieldId).stream().map(FieldCycleResponse::of).toList();
	}

	public FieldCycleResponse addCycle(UUID fieldId, UUID academicCycleId) {
		Field field = find(fieldId);
		AcademicCycle cycle = cycleService.find(academicCycleId);
		if (!cycle.isActive()) {
			throw ApiException.parentInactive("Cannot attach an INACTIVE cycle to a field");
		}
		if (fieldCycles.existsByFieldIdAndAcademicCycleId(fieldId, academicCycleId)) {
			throw new ApiException(HttpStatus.CONFLICT, "FIELD_CYCLE_EXISTS", "The field already offers this cycle");
		}
		FieldCycle fieldCycle = new FieldCycle();
		fieldCycle.setField(field);
		fieldCycle.setAcademicCycle(cycle);
		return FieldCycleResponse.of(fieldCycles.saveAndFlush(fieldCycle));
	}

	public FieldCycleResponse changeCycleStatus(UUID fieldId, UUID academicCycleId, RecordStatus status) {
		FieldCycle fieldCycle = findFieldCycle(fieldId, academicCycleId);
		fieldCycle.setStatus(status);
		return FieldCycleResponse.of(fieldCycles.saveAndFlush(fieldCycle));
	}

	public void removeCycle(UUID fieldId, UUID academicCycleId) {
		fieldCycles.delete(findFieldCycle(fieldId, academicCycleId));
	}

	private FieldCycle findFieldCycle(UUID fieldId, UUID academicCycleId) {
		find(fieldId);
		return fieldCycles.findByFieldIdAndAcademicCycleId(fieldId, academicCycleId)
				.orElseThrow(() -> ApiException.notFound("FIELD_CYCLE_NOT_FOUND", "Cycle for this field"));
	}

	Field find(UUID id) {
		return fields.findById(id).orElseThrow(() -> ApiException.notFound("FIELD_NOT_FOUND", "Field"));
	}

	private Department activeDepartment(UUID departmentId) {
		Department department = departmentService.find(departmentId);
		if (!department.isActive()) {
			throw ApiException.parentInactive("Cannot attach a field to an INACTIVE department");
		}
		return department;
	}

	private void ensureCodeFree(String code) {
		if (fields.existsByCode(code)) {
			throw ApiException.codeTaken(code);
		}
	}
}

package com.groupetp1.student_service.academic;

import java.util.UUID;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.groupetp1.student_service.academic.AcademicDtos.DepartmentRequest;
import com.groupetp1.student_service.academic.AcademicDtos.DepartmentResponse;
import com.groupetp1.student_service.common.ApiException;
import com.groupetp1.student_service.common.Codes;
import com.groupetp1.student_service.common.RecordStatus;
import com.groupetp1.student_service.common.Specs;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
@Transactional
public class DepartmentService {

	private final DepartmentRepository departments;
	private final FieldRepository fields;
	private final FacultyService facultyService;

	@Transactional(readOnly = true)
	public Page<DepartmentResponse> list(UUID facultyId, RecordStatus status, String q, Pageable pageable) {
		return departments.findAll(Specs.<Department>catalog(status, q, (root, cb, predicates) -> {
			if (facultyId != null) {
				predicates.add(cb.equal(root.get("faculty").get("id"), facultyId));
			}
		}), pageable).map(DepartmentResponse::of);
	}

	@Transactional(readOnly = true)
	public DepartmentResponse get(UUID id) {
		return DepartmentResponse.of(find(id));
	}

	public DepartmentResponse create(DepartmentRequest request) {
		ensureCodeFree(Codes.normalize(request.code()));
		Department department = new Department();
		department.setFaculty(activeFaculty(request.facultyId()));
		request.applyTo(department);
		return DepartmentResponse.of(departments.saveAndFlush(department));
	}

	public DepartmentResponse update(UUID id, DepartmentRequest request) {
		Department department = find(id);
		String code = Codes.normalize(request.code());
		if (!code.equals(department.getCode())) {
			ensureCodeFree(code);
		}
		if (!department.getFaculty().getId().equals(request.facultyId())) {
			department.setFaculty(activeFaculty(request.facultyId()));
		}
		request.applyTo(department);
		return DepartmentResponse.of(departments.saveAndFlush(department));
	}

	public DepartmentResponse changeStatus(UUID id, RecordStatus status) {
		Department department = find(id);
		department.setStatus(status);
		return DepartmentResponse.of(departments.saveAndFlush(department));
	}

	public void delete(UUID id) {
		Department department = find(id);
		if (fields.existsByDepartmentId(id)) {
			throw ApiException.inUse("The department still has fields; delete them or set the department INACTIVE");
		}
		departments.delete(department);
	}

	Department find(UUID id) {
		return departments.findById(id)
				.orElseThrow(() -> ApiException.notFound("DEPARTMENT_NOT_FOUND", "Department"));
	}

	private Faculty activeFaculty(UUID facultyId) {
		Faculty faculty = facultyService.find(facultyId);
		if (!faculty.isActive()) {
			throw ApiException.parentInactive("Cannot attach a department to an INACTIVE faculty");
		}
		return faculty;
	}

	private void ensureCodeFree(String code) {
		if (departments.existsByCode(code)) {
			throw ApiException.codeTaken(code);
		}
	}
}

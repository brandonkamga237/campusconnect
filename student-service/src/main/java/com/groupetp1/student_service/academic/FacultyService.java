package com.groupetp1.student_service.academic;

import java.util.UUID;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.groupetp1.student_service.academic.AcademicDtos.FacultyRequest;
import com.groupetp1.student_service.academic.AcademicDtos.FacultyResponse;
import com.groupetp1.student_service.common.ApiException;
import com.groupetp1.student_service.common.Codes;
import com.groupetp1.student_service.common.RecordStatus;
import com.groupetp1.student_service.common.Specs;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
@Transactional
public class FacultyService {

	private final FacultyRepository faculties;
	private final DepartmentRepository departments;

	@Transactional(readOnly = true)
	public Page<FacultyResponse> list(RecordStatus status, String q, Pageable pageable) {
		return faculties.findAll(Specs.catalog(status, q, null), pageable).map(FacultyResponse::of);
	}

	@Transactional(readOnly = true)
	public FacultyResponse get(UUID id) {
		return FacultyResponse.of(find(id));
	}

	public FacultyResponse create(FacultyRequest request) {
		ensureCodeFree(Codes.normalize(request.code()));
		Faculty faculty = new Faculty();
		request.applyTo(faculty);
		return FacultyResponse.of(faculties.saveAndFlush(faculty));
	}

	public FacultyResponse update(UUID id, FacultyRequest request) {
		Faculty faculty = find(id);
		String code = Codes.normalize(request.code());
		if (!code.equals(faculty.getCode())) {
			ensureCodeFree(code);
		}
		request.applyTo(faculty);
		return FacultyResponse.of(faculties.saveAndFlush(faculty));
	}

	public FacultyResponse changeStatus(UUID id, RecordStatus status) {
		Faculty faculty = find(id);
		faculty.setStatus(status);
		return FacultyResponse.of(faculties.saveAndFlush(faculty));
	}

	public void delete(UUID id) {
		Faculty faculty = find(id);
		if (departments.existsByFacultyId(id)) {
			throw ApiException.inUse("The faculty still has departments; delete them or set the faculty INACTIVE");
		}
		faculties.delete(faculty);
	}

	Faculty find(UUID id) {
		return faculties.findById(id).orElseThrow(() -> ApiException.notFound("FACULTY_NOT_FOUND", "Faculty"));
	}

	private void ensureCodeFree(String code) {
		if (faculties.existsByCode(code)) {
			throw ApiException.codeTaken(code);
		}
	}
}

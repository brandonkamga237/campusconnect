package com.groupetp1.student_service.academic;

import java.util.List;
import java.util.UUID;

import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.groupetp1.student_service.academic.AcademicDtos.AcademicCycleRequest;
import com.groupetp1.student_service.academic.AcademicDtos.AcademicCycleResponse;
import com.groupetp1.student_service.academic.AcademicDtos.StudyLevelRequest;
import com.groupetp1.student_service.academic.AcademicDtos.StudyLevelResponse;
import com.groupetp1.student_service.common.ApiException;
import com.groupetp1.student_service.common.Codes;
import com.groupetp1.student_service.common.RecordStatus;

import lombok.RequiredArgsConstructor;

/** Cycles et niveaux d'études. */
@Service
@RequiredArgsConstructor
@Transactional
public class AcademicCycleService {

	private final AcademicCycleRepository cycles;
	private final StudyLevelRepository levels;
	private final FieldCycleRepository fieldCycles;

	// --- cycles -----------------------------------------------------------------------------

	@Transactional(readOnly = true)
	public List<AcademicCycleResponse> list(RecordStatus status) {
		List<AcademicCycle> found = status == null ? cycles.findAllByOrderByCode()
				: cycles.findByStatusOrderByCode(status);
		return found.stream().map(AcademicCycleResponse::of).toList();
	}

	@Transactional(readOnly = true)
	public AcademicCycleResponse get(UUID id) {
		return AcademicCycleResponse.of(find(id));
	}

	public AcademicCycleResponse create(AcademicCycleRequest request) {
		ensureCycleCodeFree(Codes.normalize(request.code()));
		AcademicCycle cycle = new AcademicCycle();
		request.applyTo(cycle);
		return AcademicCycleResponse.of(cycles.saveAndFlush(cycle));
	}

	public AcademicCycleResponse update(UUID id, AcademicCycleRequest request) {
		AcademicCycle cycle = find(id);
		String code = Codes.normalize(request.code());
		if (!code.equals(cycle.getCode())) {
			ensureCycleCodeFree(code);
		}
		request.applyTo(cycle);
		return AcademicCycleResponse.of(cycles.saveAndFlush(cycle));
	}

	public AcademicCycleResponse changeStatus(UUID id, RecordStatus status) {
		AcademicCycle cycle = find(id);
		cycle.setStatus(status);
		return AcademicCycleResponse.of(cycles.saveAndFlush(cycle));
	}

	public void delete(UUID id) {
		AcademicCycle cycle = find(id);
		if (levels.existsByAcademicCycleId(id)) {
			throw ApiException.inUse("The cycle still has study levels; delete them or set the cycle INACTIVE");
		}
		if (fieldCycles.existsByAcademicCycleId(id)) {
			throw ApiException.inUse("Fields still offer this cycle; detach it or set the cycle INACTIVE");
		}
		cycles.delete(cycle);
	}

	AcademicCycle find(UUID id) {
		return cycles.findById(id).orElseThrow(() -> ApiException.notFound("ACADEMIC_CYCLE_NOT_FOUND", "Academic cycle"));
	}

	private void ensureCycleCodeFree(String code) {
		if (cycles.existsByCode(code)) {
			throw ApiException.codeTaken(code);
		}
	}

	// --- niveaux ----------------------------------------------------------------------------

	@Transactional(readOnly = true)
	public List<StudyLevelResponse> listLevels(UUID academicCycleId) {
		List<StudyLevel> found;
		if (academicCycleId == null) {
			found = levels.findAllByOrderByAcademicCycleCodeAscPositionAsc();
		} else {
			find(academicCycleId);
			found = levels.findByAcademicCycleIdOrderByPosition(academicCycleId);
		}
		return found.stream().map(StudyLevelResponse::of).toList();
	}

	@Transactional(readOnly = true)
	public StudyLevelResponse getLevel(UUID id) {
		return StudyLevelResponse.of(findLevel(id));
	}

	public StudyLevelResponse createLevel(StudyLevelRequest request) {
		String code = Codes.normalize(request.code());
		if (levels.existsByCode(code)) {
			throw ApiException.codeTaken(code);
		}
		AcademicCycle cycle = find(request.academicCycleId());
		ensurePositionFree(cycle.getId(), request.position());
		StudyLevel level = new StudyLevel();
		level.setAcademicCycle(cycle);
		applyLevel(level, code, request);
		return StudyLevelResponse.of(levels.saveAndFlush(level));
	}

	public StudyLevelResponse updateLevel(UUID id, StudyLevelRequest request) {
		StudyLevel level = findLevel(id);
		String code = Codes.normalize(request.code());
		if (!code.equals(level.getCode()) && levels.existsByCode(code)) {
			throw ApiException.codeTaken(code);
		}
		boolean cycleChanged = !level.getAcademicCycle().getId().equals(request.academicCycleId());
		if (cycleChanged || !level.getPosition().equals(request.position())) {
			AcademicCycle cycle = cycleChanged ? find(request.academicCycleId()) : level.getAcademicCycle();
			ensurePositionFree(cycle.getId(), request.position());
			level.setAcademicCycle(cycle);
		}
		applyLevel(level, code, request);
		return StudyLevelResponse.of(levels.saveAndFlush(level));
	}

	public void deleteLevel(UUID id) {
		levels.delete(findLevel(id));
	}

	private StudyLevel findLevel(UUID id) {
		return levels.findById(id).orElseThrow(() -> ApiException.notFound("STUDY_LEVEL_NOT_FOUND", "Study level"));
	}

	private void ensurePositionFree(UUID cycleId, Integer position) {
		if (levels.existsByAcademicCycleIdAndPosition(cycleId, position)) {
			throw new ApiException(HttpStatus.CONFLICT, "POSITION_TAKEN",
					"Another level of this cycle already has position " + position);
		}
	}

	private static void applyLevel(StudyLevel level, String code, StudyLevelRequest request) {
		level.setCode(code);
		level.setName(request.name().trim());
		level.setPosition(request.position());
	}
}

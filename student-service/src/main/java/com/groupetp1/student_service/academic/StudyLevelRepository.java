package com.groupetp1.student_service.academic;

import java.util.List;
import java.util.UUID;

import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;

public interface StudyLevelRepository extends JpaRepository<StudyLevel, UUID> {

	boolean existsByCode(String code);

	boolean existsByAcademicCycleIdAndPosition(UUID academicCycleId, Integer position);

	boolean existsByAcademicCycleId(UUID academicCycleId);

	@EntityGraph(attributePaths = "academicCycle")
	List<StudyLevel> findByAcademicCycleIdOrderByPosition(UUID academicCycleId);

	@EntityGraph(attributePaths = "academicCycle")
	List<StudyLevel> findAllByOrderByAcademicCycleCodeAscPositionAsc();
}

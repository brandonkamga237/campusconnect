package com.groupetp1.student_service.academic;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;

public interface FieldCycleRepository extends JpaRepository<FieldCycle, UUID> {

	boolean existsByFieldIdAndAcademicCycleId(UUID fieldId, UUID academicCycleId);

	boolean existsByAcademicCycleId(UUID academicCycleId);

	@EntityGraph(attributePaths = "academicCycle")
	List<FieldCycle> findByFieldIdOrderByAcademicCycleCode(UUID fieldId);

	@EntityGraph(attributePaths = "academicCycle")
	Optional<FieldCycle> findByFieldIdAndAcademicCycleId(UUID fieldId, UUID academicCycleId);
}

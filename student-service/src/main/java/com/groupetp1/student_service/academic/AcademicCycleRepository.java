package com.groupetp1.student_service.academic;

import java.util.List;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;

import com.groupetp1.student_service.common.RecordStatus;

public interface AcademicCycleRepository extends JpaRepository<AcademicCycle, UUID> {

	boolean existsByCode(String code);

	List<AcademicCycle> findAllByOrderByCode();

	List<AcademicCycle> findByStatusOrderByCode(RecordStatus status);
}

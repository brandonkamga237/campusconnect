package com.groupetp1.student_service.academic;

import java.util.UUID;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

public interface DepartmentRepository extends JpaRepository<Department, UUID>, JpaSpecificationExecutor<Department> {

	boolean existsByCode(String code);

	boolean existsByFacultyId(UUID facultyId);

	/** Charge le parent dans la même requête (évite une requête par ligne). */
	@Override
	@EntityGraph(attributePaths = "faculty")
	Page<Department> findAll(Specification<Department> spec, Pageable pageable);
}

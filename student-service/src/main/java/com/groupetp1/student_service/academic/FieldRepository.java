package com.groupetp1.student_service.academic;

import java.util.UUID;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

public interface FieldRepository extends JpaRepository<Field, UUID>, JpaSpecificationExecutor<Field> {

	boolean existsByCode(String code);

	boolean existsByDepartmentId(UUID departmentId);

	/** Charge le parent dans la même requête (évite une requête par ligne). */
	@Override
	@EntityGraph(attributePaths = "department.faculty")
	Page<Field> findAll(Specification<Field> spec, Pageable pageable);
}

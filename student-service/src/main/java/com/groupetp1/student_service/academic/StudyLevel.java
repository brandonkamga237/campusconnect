package com.groupetp1.student_service.academic;

import java.util.UUID;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.Setter;

/** Niveau d'études (L1, L2…) ; position = ordre dans le cycle. */
@Getter
@Setter
@Entity
@Table(name = "study_levels")
public class StudyLevel {

	@Id
	@GeneratedValue(strategy = GenerationType.UUID)
	private UUID id;

	@ManyToOne(fetch = FetchType.LAZY, optional = false)
	@JoinColumn(name = "academic_cycle_id", nullable = false)
	private AcademicCycle academicCycle;

	@Column(nullable = false, unique = true, length = 20)
	private String code;

	@Column(nullable = false, length = 150)
	private String name;

	@Column(nullable = false)
	private Integer position;
}

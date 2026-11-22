package com.groupetp1.student_service.academic;

import java.util.UUID;

import com.groupetp1.student_service.common.RecordStatus;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.Setter;

/** Cycle proposé par une filière (ex. la filière GL propose Licence et Master). */
@Getter
@Setter
@Entity
@Table(name = "field_cycles")
public class FieldCycle {

	@Id
	@GeneratedValue(strategy = GenerationType.UUID)
	private UUID id;

	@ManyToOne(fetch = FetchType.LAZY, optional = false)
	@JoinColumn(name = "field_id", nullable = false)
	private Field field;

	@ManyToOne(fetch = FetchType.LAZY, optional = false)
	@JoinColumn(name = "academic_cycle_id", nullable = false)
	private AcademicCycle academicCycle;

	@Enumerated(EnumType.STRING)
	@Column(nullable = false, length = 16)
	private RecordStatus status = RecordStatus.ACTIVE;
}

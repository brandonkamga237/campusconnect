package com.groupetp1.student_service.academic;

import com.groupetp1.student_service.common.AuditedNamedEntity;

import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.Setter;

/** Filière. */
@Getter
@Setter
@Entity
@Table(name = "fields")
public class Field extends AuditedNamedEntity {

	@ManyToOne(fetch = FetchType.LAZY, optional = false)
	@JoinColumn(name = "department_id", nullable = false)
	private Department department;
}

package com.groupetp1.student_service.academic;

import com.groupetp1.student_service.common.AuditedNamedEntity;

import jakarta.persistence.Entity;
import jakarta.persistence.Table;

@Entity
@Table(name = "faculties")
public class Faculty extends AuditedNamedEntity {
}

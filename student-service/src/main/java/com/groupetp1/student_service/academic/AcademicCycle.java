package com.groupetp1.student_service.academic;

import com.groupetp1.student_service.common.NamedEntity;

import jakarta.persistence.Entity;
import jakarta.persistence.Table;

/** Cycle (Licence, Master, Doctorat…). */
@Entity
@Table(name = "academic_cycles")
public class AcademicCycle extends NamedEntity {
}

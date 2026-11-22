package com.groupetp1.student_service.common;

import java.util.UUID;

import jakarta.persistence.Column;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.MappedSuperclass;
import lombok.Getter;
import lombok.Setter;

/** Colonnes communes : id, code unique, nom, description, statut. */
@Getter
@Setter
@MappedSuperclass
public abstract class NamedEntity {

	@Id
	@GeneratedValue(strategy = GenerationType.UUID)
	private UUID id;

	@Column(nullable = false, unique = true, length = 20)
	private String code;

	@Column(nullable = false, length = 150)
	private String name;

	@Column(length = 1000)
	private String description;

	@Enumerated(EnumType.STRING)
	@Column(nullable = false, length = 16)
	private RecordStatus status = RecordStatus.ACTIVE;

	public Ref toRef() {
		return new Ref(id, code, name);
	}

	public boolean isActive() {
		return status == RecordStatus.ACTIVE;
	}
}

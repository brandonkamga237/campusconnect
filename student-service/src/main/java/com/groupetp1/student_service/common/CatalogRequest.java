package com.groupetp1.student_service.common;

/** Champs communs aux requêtes de création/modification d'un élément nommé. */
public interface CatalogRequest {

	String code();

	String name();

	String description();

	default void applyTo(NamedEntity entity) {
		entity.setCode(Codes.normalize(code()));
		entity.setName(name().trim());
		entity.setDescription(description() == null || description().isBlank() ? null : description().trim());
	}
}

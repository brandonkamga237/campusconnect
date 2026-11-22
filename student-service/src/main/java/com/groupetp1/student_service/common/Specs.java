package com.groupetp1.student_service.common;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

import org.springframework.data.jpa.domain.Specification;

import jakarta.persistence.criteria.CriteriaBuilder;
import jakarta.persistence.criteria.Predicate;
import jakarta.persistence.criteria.Root;

/** Filtres de liste communs : statut + recherche texte (code ou nom), plus des filtres propres à chaque entité. */
public final class Specs {

	private Specs() {
	}

	@FunctionalInterface
	public interface Extra<T> {
		void add(Root<T> root, CriteriaBuilder cb, List<Predicate> predicates);
	}

	public static <T> Specification<T> catalog(RecordStatus status, String q, Extra<T> extra) {
		return (root, query, cb) -> {
			List<Predicate> predicates = new ArrayList<>();
			if (status != null) {
				predicates.add(cb.equal(root.get("status"), status));
			}
			if (q != null && !q.isBlank()) {
				String like = "%" + escapeLike(q.trim().toLowerCase(Locale.ROOT)) + "%";
				predicates.add(cb.or(
						cb.like(cb.lower(root.get("name")), like, '\\'),
						cb.like(cb.lower(root.get("code")), like, '\\')));
			}
			if (extra != null) {
				extra.add(root, cb, predicates);
			}
			return cb.and(predicates.toArray(Predicate[]::new));
		};
	}

	private static String escapeLike(String value) {
		return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_");
	}
}

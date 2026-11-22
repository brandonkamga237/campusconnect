package com.groupetp1.student_service.common;

import org.springframework.http.HttpStatus;

import lombok.Getter;

/** Erreur métier renvoyée au format RFC 9457 avec un champ {@code code} stable. */
@Getter
public class ApiException extends RuntimeException {

	private final HttpStatus status;
	private final String code;

	public ApiException(HttpStatus status, String code, String detail) {
		super(detail);
		this.status = status;
		this.code = code;
	}

	public static ApiException notFound(String code, String what) {
		return new ApiException(HttpStatus.NOT_FOUND, code, what + " not found");
	}

	public static ApiException codeTaken(String code) {
		return new ApiException(HttpStatus.CONFLICT, "CODE_TAKEN", "The code '" + code + "' is already used");
	}

	public static ApiException inUse(String detail) {
		return new ApiException(HttpStatus.CONFLICT, "RESOURCE_IN_USE", detail);
	}

	public static ApiException parentInactive(String detail) {
		return new ApiException(HttpStatus.CONFLICT, "PARENT_INACTIVE", detail);
	}
}

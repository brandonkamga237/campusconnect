package com.groupetp1.student_service.common;

import java.util.Locale;

public final class Codes {

	private Codes() {
	}

	/** Les codes sont stockés en majuscules, sans espaces autour. */
	public static String normalize(String code) {
		return code.trim().toUpperCase(Locale.ROOT);
	}
}

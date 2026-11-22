package com.groupetp1.student_service.common;

import java.util.UUID;

/** Référence courte vers un élément parent dans les réponses JSON. */
public record Ref(UUID id, String code, String name) {
}

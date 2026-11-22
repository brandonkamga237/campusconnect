package com.groupetp1.student_service.common;

import jakarta.validation.constraints.NotNull;

public record StatusRequest(@NotNull RecordStatus status) {
}

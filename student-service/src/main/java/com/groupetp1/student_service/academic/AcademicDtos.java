package com.groupetp1.student_service.academic;

import java.time.Instant;
import java.util.UUID;

import com.groupetp1.student_service.common.CatalogRequest;
import com.groupetp1.student_service.common.RecordStatus;
import com.groupetp1.student_service.common.Ref;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/** Corps des requêtes et des réponses JSON du référentiel académique. */
public final class AcademicDtos {

	private AcademicDtos() {
	}

	private static final String CODE_REGEX = "^[A-Za-z0-9_-]+$";
	private static final String CODE_MESSAGE = "letters, digits, '-' and '_' only";

	// --- facultés -------------------------------------------------------------------------

	public record FacultyRequest(
			@NotBlank @Size(max = 20) @Pattern(regexp = CODE_REGEX, message = CODE_MESSAGE) String code,
			@NotBlank @Size(max = 150) String name,
			@Size(max = 1000) String description) implements CatalogRequest {
	}

	public record FacultyResponse(UUID id, String code, String name, String description, RecordStatus status,
			Instant createdAt, Instant updatedAt) {

		static FacultyResponse of(Faculty f) {
			return new FacultyResponse(f.getId(), f.getCode(), f.getName(), f.getDescription(), f.getStatus(),
					f.getCreatedAt(), f.getUpdatedAt());
		}
	}

	// --- départements ---------------------------------------------------------------------

	public record DepartmentRequest(
			@NotNull UUID facultyId,
			@NotBlank @Size(max = 20) @Pattern(regexp = CODE_REGEX, message = CODE_MESSAGE) String code,
			@NotBlank @Size(max = 150) String name,
			@Size(max = 1000) String description) implements CatalogRequest {
	}

	public record DepartmentResponse(UUID id, Ref faculty, String code, String name, String description,
			RecordStatus status, Instant createdAt, Instant updatedAt) {

		static DepartmentResponse of(Department d) {
			return new DepartmentResponse(d.getId(), d.getFaculty().toRef(), d.getCode(), d.getName(),
					d.getDescription(), d.getStatus(), d.getCreatedAt(), d.getUpdatedAt());
		}
	}

	// --- filières -------------------------------------------------------------------------

	public record FieldRequest(
			@NotNull UUID departmentId,
			@NotBlank @Size(max = 20) @Pattern(regexp = CODE_REGEX, message = CODE_MESSAGE) String code,
			@NotBlank @Size(max = 150) String name,
			@Size(max = 1000) String description) implements CatalogRequest {
	}

	public record FieldResponse(UUID id, Ref department, Ref faculty, String code, String name, String description,
			RecordStatus status, Instant createdAt, Instant updatedAt) {

		static FieldResponse of(Field f) {
			Department d = f.getDepartment();
			return new FieldResponse(f.getId(), d.toRef(), d.getFaculty().toRef(), f.getCode(), f.getName(),
					f.getDescription(), f.getStatus(), f.getCreatedAt(), f.getUpdatedAt());
		}
	}

	// --- cycles ---------------------------------------------------------------------------

	public record AcademicCycleRequest(
			@NotBlank @Size(max = 20) @Pattern(regexp = CODE_REGEX, message = CODE_MESSAGE) String code,
			@NotBlank @Size(max = 150) String name,
			@Size(max = 1000) String description) implements CatalogRequest {
	}

	public record AcademicCycleResponse(UUID id, String code, String name, String description, RecordStatus status) {

		static AcademicCycleResponse of(AcademicCycle c) {
			return new AcademicCycleResponse(c.getId(), c.getCode(), c.getName(), c.getDescription(), c.getStatus());
		}
	}

	// --- niveaux --------------------------------------------------------------------------

	public record StudyLevelRequest(
			@NotNull UUID academicCycleId,
			@NotBlank @Size(max = 20) @Pattern(regexp = CODE_REGEX, message = CODE_MESSAGE) String code,
			@NotBlank @Size(max = 150) String name,
			@NotNull @Min(1) @Max(20) Integer position) {
	}

	public record StudyLevelResponse(UUID id, Ref academicCycle, String code, String name, Integer position) {

		static StudyLevelResponse of(StudyLevel l) {
			return new StudyLevelResponse(l.getId(), l.getAcademicCycle().toRef(), l.getCode(), l.getName(),
					l.getPosition());
		}
	}

	// --- cycles d'une filière -------------------------------------------------------------

	public record FieldCycleRequest(@NotNull UUID academicCycleId) {
	}

	public record FieldCycleResponse(UUID id, UUID fieldId, Ref academicCycle, RecordStatus status) {

		static FieldCycleResponse of(FieldCycle fc) {
			return new FieldCycleResponse(fc.getId(), fc.getField().getId(), fc.getAcademicCycle().toRef(),
					fc.getStatus());
		}
	}
}

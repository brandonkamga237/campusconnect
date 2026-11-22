-- Structure académique : facultés > départements > filières, cycles > niveaux, filières <-> cycles.

CREATE TABLE faculties (
    id          UUID PRIMARY KEY,
    code        VARCHAR(20)   NOT NULL UNIQUE,
    name        VARCHAR(150)  NOT NULL,
    description VARCHAR(1000),
    status      VARCHAR(16)   NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),
    created_at  TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ   NOT NULL DEFAULT now()
);

CREATE TABLE departments (
    id          UUID PRIMARY KEY,
    faculty_id  UUID          NOT NULL REFERENCES faculties (id),
    code        VARCHAR(20)   NOT NULL UNIQUE,
    name        VARCHAR(150)  NOT NULL,
    description VARCHAR(1000),
    status      VARCHAR(16)   NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),
    created_at  TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ   NOT NULL DEFAULT now()
);
CREATE INDEX ix_departments_faculty ON departments (faculty_id);

CREATE TABLE fields (
    id            UUID PRIMARY KEY,
    department_id UUID          NOT NULL REFERENCES departments (id),
    code          VARCHAR(20)   NOT NULL UNIQUE,
    name          VARCHAR(150)  NOT NULL,
    description   VARCHAR(1000),
    status        VARCHAR(16)   NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),
    created_at    TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ   NOT NULL DEFAULT now()
);
CREATE INDEX ix_fields_department ON fields (department_id);

CREATE TABLE academic_cycles (
    id          UUID PRIMARY KEY,
    code        VARCHAR(20)   NOT NULL UNIQUE,
    name        VARCHAR(150)  NOT NULL,
    description VARCHAR(1000),
    status      VARCHAR(16)   NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE'))
);

CREATE TABLE study_levels (
    id                UUID PRIMARY KEY,
    academic_cycle_id UUID         NOT NULL REFERENCES academic_cycles (id),
    code              VARCHAR(20)  NOT NULL UNIQUE,
    name              VARCHAR(150) NOT NULL,
    position          INTEGER      NOT NULL CHECK (position > 0),
    CONSTRAINT uq_study_levels_cycle_position UNIQUE (academic_cycle_id, position)
);

CREATE TABLE field_cycles (
    id                UUID PRIMARY KEY,
    field_id          UUID        NOT NULL REFERENCES fields (id) ON DELETE CASCADE,
    academic_cycle_id UUID        NOT NULL REFERENCES academic_cycles (id),
    status            VARCHAR(16) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),
    CONSTRAINT uq_field_cycles UNIQUE (field_id, academic_cycle_id)
);
CREATE INDEX ix_field_cycles_cycle ON field_cycles (academic_cycle_id);

-- Données de référence du système LMD (modifiables ensuite via l'API).
INSERT INTO academic_cycles (id, code, name, description) VALUES
    ('00000000-0000-0000-0000-000000000001', 'LICENCE',  'Licence',  'Premier cycle, 3 ans'),
    ('00000000-0000-0000-0000-000000000002', 'MASTER',   'Master',   'Deuxième cycle, 2 ans'),
    ('00000000-0000-0000-0000-000000000003', 'DOCTORAT', 'Doctorat', 'Troisième cycle, 3 ans');

INSERT INTO study_levels (id, academic_cycle_id, code, name, position) VALUES
    (gen_random_uuid(), '00000000-0000-0000-0000-000000000001', 'L1', 'Licence 1', 1),
    (gen_random_uuid(), '00000000-0000-0000-0000-000000000001', 'L2', 'Licence 2', 2),
    (gen_random_uuid(), '00000000-0000-0000-0000-000000000001', 'L3', 'Licence 3', 3),
    (gen_random_uuid(), '00000000-0000-0000-0000-000000000002', 'M1', 'Master 1', 1),
    (gen_random_uuid(), '00000000-0000-0000-0000-000000000002', 'M2', 'Master 2', 2),
    (gen_random_uuid(), '00000000-0000-0000-0000-000000000003', 'D1', 'Doctorat 1', 1),
    (gen_random_uuid(), '00000000-0000-0000-0000-000000000003', 'D2', 'Doctorat 2', 2),
    (gen_random_uuid(), '00000000-0000-0000-0000-000000000003', 'D3', 'Doctorat 3', 3);

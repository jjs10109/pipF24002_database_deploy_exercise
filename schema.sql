-- Intake responses from class_dataset.csv.
-- One row per student. tools and availability are many-to-many.
-- interests stays free text.

CREATE TABLE students (
    student_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    identifier VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    school_year VARCHAR(20) NOT NULL CHECK (school_year IN ('First-year', 'Sophomore', 'Junior', 'Senior')),
    intro_programming VARCHAR(20) NOT NULL CHECK (intro_programming IN ('took_it', 'equivalent', 'neither')),
    skill_programming SMALLINT NOT NULL CHECK (skill_programming BETWEEN 1 AND 5),
    skill_data_stats SMALLINT NOT NULL CHECK (skill_data_stats BETWEEN 1 AND 5),
    skill_frontend_design SMALLINT NOT NULL CHECK (skill_frontend_design BETWEEN 1 AND 5),
    skill_business_pitch SMALLINT NOT NULL CHECK (skill_business_pitch BETWEEN 1 AND 5),
    working_style TEXT,
    interests TEXT,
    semester_goal TEXT,
    submitted_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE tools (
    tool_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(32) NOT NULL UNIQUE
);

CREATE TABLE student_tools (
    student_id INTEGER NOT NULL REFERENCES students (student_id) ON DELETE CASCADE,
    tool_id INTEGER NOT NULL REFERENCES tools (tool_id),
    PRIMARY KEY (student_id, tool_id)
);

CREATE TABLE availability_slots (
    slot_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    period VARCHAR(10) NOT NULL CHECK (period IN ('weekday', 'weekend')),
    time_of_day VARCHAR(10) NOT NULL CHECK (time_of_day IN ('morning', 'afternoon', 'evening')),
    UNIQUE (period, time_of_day)
);

CREATE TABLE student_availability (
    student_id INTEGER NOT NULL REFERENCES students (student_id) ON DELETE CASCADE,
    slot_id INTEGER NOT NULL REFERENCES availability_slots (slot_id),
    PRIMARY KEY (student_id, slot_id)
);

INSERT INTO tools (name) VALUES
    ('Python'),
    ('SQL'),
    ('Excel'),
    ('JavaScript'),
    ('R');

INSERT INTO availability_slots (period, time_of_day) VALUES
    ('weekday', 'morning'),
    ('weekday', 'afternoon'),
    ('weekday', 'evening'),
    ('weekend', 'morning'),
    ('weekend', 'afternoon'),
    ('weekend', 'evening');

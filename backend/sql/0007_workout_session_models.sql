-- Migration SQL for: apps.training 0007_workout_session_models
-- Target DB: PostgreSQL (Dev)
-- Notes:
--   1) Run once (equivalent to pending Django migration).
--   2) Run inside a transaction.
--   3) Marks migration as applied in django_migrations.

BEGIN;

CREATE TABLE training_workout_sessions (
    id BIGSERIAL PRIMARY KEY,
    session_date DATE NOT NULL DEFAULT CURRENT_DATE,
    workout_type VARCHAR(20) NOT NULL DEFAULT 'video_workout',
    status VARCHAR(20) NOT NULL DEFAULT 'in_progress',
    title VARCHAR(200) NOT NULL DEFAULT '',
    video_name VARCHAR(200) NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    ai_summary TEXT NOT NULL DEFAULT '',
    completed_at TIMESTAMPTZ NULL,
    total_exercises INTEGER NOT NULL DEFAULT 0,
    total_sets INTEGER NOT NULL DEFAULT 0,
    total_reps INTEGER NOT NULL DEFAULT 0,
    total_volume NUMERIC(12, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id BIGINT NOT NULL,
    CONSTRAINT training_workout_sessions_user_id_fk
        FOREIGN KEY (user_id)
        REFERENCES users (id)
        ON DELETE CASCADE
);

CREATE INDEX training_wo_user_id_4202a8_idx
    ON training_workout_sessions (user_id, session_date);

CREATE TABLE training_workout_exercises (
    id BIGSERIAL PRIMARY KEY,
    exercise_name VARCHAR(200) NOT NULL,
    "order" SMALLINT NOT NULL DEFAULT 1,
    notes TEXT NOT NULL DEFAULT '',
    intensity SMALLINT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    workout_session_id BIGINT NOT NULL,
    CONSTRAINT training_workout_exercises_session_id_fk
        FOREIGN KEY (workout_session_id)
        REFERENCES training_workout_sessions (id)
        ON DELETE CASCADE
);

CREATE INDEX training_wo_workout_0e6ffb_idx
    ON training_workout_exercises (workout_session_id, "order");

CREATE TABLE training_exercise_sets (
    id BIGSERIAL PRIMARY KEY,
    set_number SMALLINT NOT NULL,
    reps SMALLINT NULL,
    weight_kg NUMERIC(7, 2) NULL,
    intensity SMALLINT NULL,
    rest_seconds INTEGER NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    workout_exercise_id BIGINT NOT NULL,
    CONSTRAINT training_exercise_sets_workout_exercise_id_fk
        FOREIGN KEY (workout_exercise_id)
        REFERENCES training_workout_exercises (id)
        ON DELETE CASCADE
);

ALTER TABLE training_exercise_sets
    ADD CONSTRAINT training_exercise_sets_exercise_set_number_unique
    UNIQUE (workout_exercise_id, set_number);

-- Positive/validator-aligned checks
ALTER TABLE training_workout_sessions
    ADD CONSTRAINT training_workout_sessions_total_exercises_non_negative
    CHECK (total_exercises >= 0);
ALTER TABLE training_workout_sessions
    ADD CONSTRAINT training_workout_sessions_total_sets_non_negative
    CHECK (total_sets >= 0);
ALTER TABLE training_workout_sessions
    ADD CONSTRAINT training_workout_sessions_total_reps_non_negative
    CHECK (total_reps >= 0);
ALTER TABLE training_workout_sessions
    ADD CONSTRAINT training_workout_sessions_workout_type_valid
    CHECK (workout_type IN ('video_workout', 'gym_workout'));
ALTER TABLE training_workout_sessions
    ADD CONSTRAINT training_workout_sessions_status_valid
    CHECK (status IN ('in_progress', 'completed'));

ALTER TABLE training_workout_exercises
    ADD CONSTRAINT training_workout_exercises_order_non_negative
    CHECK ("order" >= 0);
ALTER TABLE training_workout_exercises
    ADD CONSTRAINT training_workout_exercises_intensity_range
    CHECK (intensity IS NULL OR intensity BETWEEN 1 AND 10);

ALTER TABLE training_exercise_sets
    ADD CONSTRAINT training_exercise_sets_set_number_min_1
    CHECK (set_number >= 1);
ALTER TABLE training_exercise_sets
    ADD CONSTRAINT training_exercise_sets_reps_non_negative
    CHECK (reps IS NULL OR reps >= 0);
ALTER TABLE training_exercise_sets
    ADD CONSTRAINT training_exercise_sets_intensity_range
    CHECK (intensity IS NULL OR intensity BETWEEN 1 AND 10);
ALTER TABLE training_exercise_sets
    ADD CONSTRAINT training_exercise_sets_rest_seconds_non_negative
    CHECK (rest_seconds IS NULL OR rest_seconds >= 0);

INSERT INTO django_migrations (app, name, applied)
SELECT 'training', '0007_workout_session_models', NOW()
WHERE NOT EXISTS (
    SELECT 1
    FROM django_migrations
    WHERE app = 'training' AND name = '0007_workout_session_models'
);

COMMIT;

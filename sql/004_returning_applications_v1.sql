-- Glen Moniques SMS — Returning student applications (review queue only)
-- Run only on an approved staging environment after backup and review.
-- Does NOT alter applications, registrations, or student_accounts.
BEGIN;
CREATE TABLE IF NOT EXISTS public.returning_applications (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_number varchar NOT NULL REFERENCES public.applications(student_number) ON DELETE RESTRICT,
    previous_registration_id uuid NOT NULL REFERENCES public.registrations(id) ON DELETE RESTRICT,
    target_course_code varchar NOT NULL REFERENCES public.courses(course_code) ON DELETE RESTRICT,
    target_cycle_code varchar NOT NULL REFERENCES public.cycles(cycle_code) ON DELETE RESTRICT,
    status varchar(24) NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending','UnderReview','Rejected')),
    submitted_at timestamptz NOT NULL DEFAULT now(),
    reviewed_at timestamptz,
    reviewed_by varchar,
    review_note text,
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS returning_applications_one_open_per_student
    ON public.returning_applications(student_number)
    WHERE status IN ('Pending','UnderReview');
CREATE INDEX IF NOT EXISTS returning_applications_student_history
    ON public.returning_applications(student_number,submitted_at DESC);
CREATE INDEX IF NOT EXISTS returning_applications_review_queue
    ON public.returning_applications(status,submitted_at DESC);
-- All access is through authenticated backend with server-side ownership checks.
ALTER TABLE public.returning_applications ENABLE ROW LEVEL SECURITY;
COMMIT;

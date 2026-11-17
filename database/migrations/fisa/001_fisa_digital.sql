-- Glen Moniques SMS / FISA Digital Workflow V1
-- REVIEW before executing in Supabase SQL Editor. No existing tables changed.
-- Staff/learner access is enforced by authenticated FastAPI endpoints.
-- These tables deliberately have no anon/authenticated policies.
CREATE TABLE IF NOT EXISTS public.gm_fisa_sittings (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 course_code text NOT NULL,
 cycle text NOT NULL,
 title text NOT NULL,
 assessment_date date NOT NULL,
 submission_deadline timestamptz,
 assessor_code text NOT NULL,
 moderator_code text NOT NULL,
 criteria jsonb NOT NULL DEFAULT '[]'::jsonb,
 status text NOT NULL DEFAULT 'Open' CHECK (status IN ('Open','Closed')),
 rubric_path text,
 rubric_sha256 text,
 qa_report_path text,
 qa_report_sha256 text,
 qa_report_reference text,
 qa_uploaded_by text,
 qa_uploaded_at timestamptz,
 created_by text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(),
 CHECK (assessor_code <> moderator_code),
 CHECK (jsonb_typeof(criteria) = 'array')
);
CREATE TABLE IF NOT EXISTS public.gm_fisa_scripts (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 sitting_id uuid NOT NULL REFERENCES public.gm_fisa_sittings(id),
 student_number text NOT NULL,
 script_path text NOT NULL,
 script_sha256 text NOT NULL,
 script_name text NOT NULL,
 mime_type text NOT NULL,
 submitted_at timestamptz NOT NULL DEFAULT now(),
 status text NOT NULL DEFAULT 'Submitted' CHECK (status IN
 ('Submitted','Assessed','Moderated','Rendered','Internally Approved','Published','Returned')),
 assessor_decisions jsonb,
 assessor_annotations jsonb,
 assessor_comment text,
 assessed_at timestamptz,
 moderator_decisions jsonb,
 moderator_annotations jsonb,
 moderator_comment text,
 moderated_at timestamptz,
 rendered_outcome text CHECK (rendered_outcome IN ('C','NYC')),
 rendered_at timestamptz,
 approved_by text,
 approved_at timestamptz,
 published_by text,
 published_at timestamptz,
 updated_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(sitting_id,student_number)
);
CREATE TABLE IF NOT EXISTS public.gm_fisa_events (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 script_id uuid REFERENCES public.gm_fisa_scripts(id),
 sitting_id uuid NOT NULL REFERENCES public.gm_fisa_sittings(id),
 actor_code text NOT NULL,
 action text NOT NULL,
 details jsonb NOT NULL DEFAULT '{}'::jsonb,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS gm_fisa_scripts_sitting_idx ON public.gm_fisa_scripts(sitting_id,status);
CREATE INDEX IF NOT EXISTS gm_fisa_events_sitting_idx ON public.gm_fisa_events(sitting_id,created_at);
ALTER TABLE public.gm_fisa_sittings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.gm_fisa_scripts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.gm_fisa_events ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.gm_fisa_sittings,public.gm_fisa_scripts,public.gm_fisa_events FROM anon,authenticated;
REVOKE ALL ON SEQUENCE public.gm_fisa_events_id_seq FROM anon,authenticated;
-- Documents saved in existing PRIVATE Supabase Storage bucket 'student-documents'
-- Backend service-role credentials only. Never expose that key to web/mobile clients.

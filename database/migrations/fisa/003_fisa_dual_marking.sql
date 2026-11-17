-- Glen Moniques SMS FISA Dual Marking Methods V1.3
-- ADDITIVE migration; execute only after reviewing and backing up production.
-- Not a publication event; does not update learner marks.
BEGIN;
ALTER TABLE public.gm_fisa_sittings
  ADD COLUMN IF NOT EXISTS marking_method text NOT NULL DEFAULT 'competency',
  ADD COLUMN IF NOT EXISTS criterion_max_marks jsonb NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS pass_percentage numeric(6,2);
ALTER TABLE public.gm_fisa_scripts
  ADD COLUMN IF NOT EXISTS rendered_percentage numeric(6,2),
  ADD COLUMN IF NOT EXISTS rendered_total numeric(12,2),
  ADD COLUMN IF NOT EXISTS rendered_maximum numeric(12,2);
ALTER TABLE public.gm_fisa_sittings
  DROP CONSTRAINT IF EXISTS gm_fisa_sittings_marking_method_check;
ALTER TABLE public.gm_fisa_sittings
  ADD CONSTRAINT gm_fisa_sittings_marking_method_check
  CHECK (marking_method IN ('competency','percentage'));
ALTER TABLE public.gm_fisa_sittings
  DROP CONSTRAINT IF EXISTS gm_fisa_sittings_percentage_settings_check;
ALTER TABLE public.gm_fisa_sittings
  ADD CONSTRAINT gm_fisa_sittings_percentage_settings_check
  CHECK (marking_method = 'competency' OR
       (jsonb_typeof(criterion_max_marks)='array'
        AND jsonb_array_length(criterion_max_marks)=jsonb_array_length(criteria)
        AND pass_percentage BETWEEN 0 AND 100));
ALTER TABLE public.gm_fisa_scripts
  DROP CONSTRAINT IF EXISTS gm_fisa_scripts_rendered_outcome_check;
ALTER TABLE public.gm_fisa_scripts
  ADD CONSTRAINT gm_fisa_scripts_rendered_outcome_check
  CHECK (rendered_outcome IN ('C','NYC','Pass','Fail'));
-- Existing tables remain RLS-protected. Direct anon/authenticated access remains revoked.
COMMIT;

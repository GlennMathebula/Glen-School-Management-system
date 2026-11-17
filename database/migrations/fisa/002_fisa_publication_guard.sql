-- Glen Moniques SMS / FISA Publication Guard V1.2.1
-- Production migration. Blocks new legacy FISA publication for a
-- matching digital FISA course + cycle. Leaves EISA unchanged.
-- This does not retroactively change any existing Published records.
BEGIN;
CREATE OR REPLACE FUNCTION public.gm_block_legacy_fisa_publication()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $function$
DECLARE
    changed_to_restricted_publication boolean;
    has_digital_sitting boolean;
BEGIN
    IF NEW.assessment_type <> 'FISA' OR NEW.status <> 'Published' THEN
        RETURN NEW;
    END IF;

    IF TG_OP = 'INSERT' THEN
        changed_to_restricted_publication := true;
    ELSE
        changed_to_restricted_publication :=
            OLD.status IS DISTINCT FROM NEW.status
            OR OLD.assessment_type IS DISTINCT FROM NEW.assessment_type
            OR OLD.registration_id IS DISTINCT FROM NEW.registration_id;
    END IF;

    IF NOT changed_to_restricted_publication THEN
        RETURN NEW;
    END IF;

    SELECT EXISTS (
        SELECT 1
        FROM public.registrations r
        JOIN public.gm_fisa_sittings s
          ON s.course_code = r.course_code
         AND s.cycle = r.cycle
        WHERE r.id = NEW.registration_id
    ) INTO has_digital_sitting;

    IF has_digital_sitting THEN
        RAISE EXCEPTION
            'Legacy FISA publication blocked: digital FISA sitting controls release for this registration.'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$function$;

DROP TRIGGER IF EXISTS gm_guard_legacy_fisa_publish
    ON public.summative_assessments;

CREATE TRIGGER gm_guard_legacy_fisa_publish
BEFORE INSERT OR UPDATE OF status, assessment_type, registration_id
ON public.summative_assessments
FOR EACH ROW
EXECUTE FUNCTION public.gm_block_legacy_fisa_publication();

REVOKE ALL ON FUNCTION public.gm_block_legacy_fisa_publication()
    FROM PUBLIC, anon, authenticated;
COMMIT;

-- Read-only verification (run after applying):
-- SELECT tgname, tgenabled FROM pg_trigger
-- WHERE tgrelid = 'public.summative_assessments'::regclass
-- AND tgname = 'gm_guard_legacy_fisa_publish';

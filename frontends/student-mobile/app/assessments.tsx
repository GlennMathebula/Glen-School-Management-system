import * as A from "../src/api";
import { useLoad } from "../src/useLoad";
import { AlertBox, Badge, Card, Info, Loading, Screen } from "../src/components";

function AssessmentBlock({ name, value }: { name: string; value: any }) {
  return (
    <Card title={name}>
      <Info label="Stage" value={value?.stage || "Not Yet Captured"} />
      <Info
        label="Mark"
        value={value?.published && value?.mark != null ? `${value.mark}%` : "—"}
      />
      <Info
        label="Result"
        value={value?.published ? value?.result || "Published" : "Hidden until publication"}
      />
      <Badge value={value?.stage || "Not Yet Captured"} />
    </Card>
  );
}

export default function Assessments() {
  const { data: r, error, loading } = useLoad(A.assessment);
  if (loading) return <Loading text="Loading assessment status..." />;
  const d = r?.data || {};

  return (
    <Screen
      eyebrow="Summative Assessment"
      title="FISA & EISA"
      subtitle="Your current summative assessment stage and published outcomes."
    >
      <AlertBox error={error} />
      {!!d.programme && (
        <Card title="Programme">
          <Info label="Course" value={d.programme.course_name} />
          <Info label="Assessment Type" value={d.programme.assessment_type} />
          <Info label="Overall Stage" value={d.overall_stage} />
        </Card>
      )}
      <AssessmentBlock name="FISA" value={d.fisa} />
      {d.programme?.requires_eisa ? (
        <AssessmentBlock name="EISA" value={d.eisa} />
      ) : (
        <Card title="EISA">
          <Info label="Requirement" value="Not Required" />
        </Card>
      )}
    </Screen>
  );
}

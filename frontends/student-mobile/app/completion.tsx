import * as A from "../src/api";
import { useAuth } from "../src/auth";
import { useLoad } from "../src/useLoad";
import { downloadProtected } from "../src/files";
import { AlertBox, Button, Card, Info, Loading, Screen } from "../src/components";

export default function Completion() {
  const auth = useAuth();
  const { data: r, error, loading } = useLoad(A.completion);
  if (loading) return <Loading text="Loading completion status..." />;

  const d = r?.data || r || {};

  return (
    <Screen
      eyebrow="Completion"
      title="Completion Documents"
      subtitle="Download completion documents when programme requirements have been met."
    >
      <AlertBox error={error} />

      <Card title="Completion Status">
        <Info
          label="Programme Status"
          value={d.programme_status || d.registration_status || d.status}
        />
        <Info
          label="Completion Status"
          value={
            d.completion_status ||
            d.completion?.status ||
            d.eligibility_status ||
            "See document availability"
          }
        />
      </Card>

      <Card title="Letter of Completion">
        <Button
          title="Download / Share Letter"
          onPress={() =>
            void downloadProtected(
              "/api/student/completion-documents/letter-of-completion",
              auth.token,
              `Letter_of_Completion_${auth.meta?.student_number}.pdf`
            )
          }
        />
      </Card>

      <Card title="Graduation Letter">
        <Button
          title="Download / Share Graduation Letter"
          onPress={() =>
            void downloadProtected(
              "/api/student/completion-documents/graduation-letter",
              auth.token,
              `Graduation_Letter_${auth.meta?.student_number}.pdf`
            )
          }
        />
      </Card>
    </Screen>
  );
}

import { AlertBox, Badge, Card, Empty, Loading, Row, Screen } from "../src/components";
import * as A from "../src/api";
import { useLoad } from "../src/useLoad";

export default function Modules() {
  const { data: r, error, loading } = useLoad(A.modules);
  if (loading) return <Loading text="Loading modules..." />;

  const d = r?.data;
  const groups = [
    ["knowledge_modules", "Knowledge Modules"],
    ["practical_modules", "Practical Skills Modules"],
    ["workplace_modules", "Work Experience Modules"],
  ];

  return (
    <Screen
      eyebrow="Academic"
      title="My Modules"
      subtitle="Every module registered under your current programme."
    >
      <AlertBox error={error} />

      {groups.map(([key, title]) => {
        const rows = d?.[key] || [];
        return (
          <Card key={key} title={title}>
            {rows.length ? (
              rows.map((x: any) => (
                <Row
                  key={x.module_registration_id || x.module_code}
                  code={x.module_code}
                  title={x.module_name}
                  subtitle={`NQF ${x.nq_level || x.nqf_level || "—"} · ${x.credits || 0} credits`}
                  right={<Badge value={x.status} />}
                />
              ))
            ) : (
              <Empty title={`No ${title.toLowerCase()} registered`} />
            )}
          </Card>
        );
      })}
    </Screen>
  );
}

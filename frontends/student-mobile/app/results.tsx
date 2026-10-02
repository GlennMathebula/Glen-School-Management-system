import { View } from "react-native";
import * as A from "../src/api";
import { useLoad } from "../src/useLoad";
import { AlertBox, Badge, Card, Empty, Loading, Row, Screen, Stat } from "../src/components";

export default function Results() {
  const { data: r, error, loading } = useLoad(A.results);
  if (loading) return <Loading text="Loading results..." />;

  const d = r?.data || {};
  const s = d.summary || {};
  const rows = d.results || [];

  return (
    <Screen
      eyebrow="Academic"
      title="Module Marks & Results"
      subtitle="Only formally published results are shown."
    >
      <AlertBox error={error} />

      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 10, marginBottom: 13 }}>
        <Stat label="Published" value={s.published_modules ?? 0} />
        <Stat label="Passed" value={s.passed_modules ?? 0} />
        <Stat label="Failed" value={s.failed_modules ?? 0} />
        <Stat
          label="Average"
          value={s.average_mark != null ? `${s.average_mark}%` : "—"}
        />
      </View>

      <Card title="Published Results">
        {rows.length ? (
          rows.map((x: any) => (
            <Row
              key={x.module_registration_id}
              code={x.module_code}
              title={x.module_name}
              subtitle={`${x.module_type || ""} · ${x.credits || 0} credits · Attempt ${x.attempt_number || 1} · ${x.mark != null ? `${x.mark}%` : "—"}`}
              right={<Badge value={x.result} />}
            />
          ))
        ) : (
          <Empty
            title="No published module results yet"
            text="Draft, submitted or moderated marks remain hidden until formal publication."
          />
        )}
      </Card>
    </Screen>
  );
}

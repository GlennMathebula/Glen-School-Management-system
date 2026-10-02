import { Linking, View } from "react-native";
import * as A from "../src/api";
import { useLoad } from "../src/useLoad";
import { AlertBox, Button, Card, Empty, Loading, Row, Screen, dateZA } from "../src/components";

function Sessions({ rows }: { rows: any[] }) {
  if (!rows?.length) return <Empty title="No sessions published" />;

  return (
    <>
      {rows.map((s) => (
        <View key={s.session_id}>
          <Row
            code={s.module?.module_code || s.class_code}
            title={s.session_title}
            subtitle={`${dateZA(s.session_date)} · ${s.start_time}–${s.end_time} · ${s.delivery_mode} · ${s.venue || "Venue TBC"}`}
          />
          {s.can_join_online && !!s.join_online_url && (
            <View style={{ marginBottom: 10 }}>
              <Button
                title="Join Online"
                onPress={() => void Linking.openURL(s.join_online_url)}
              />
            </View>
          )}
        </View>
      ))}
    </>
  );
}

export default function Timetable() {
  const { data: r, error, loading } = useLoad(A.timetable);
  if (loading) return <Loading text="Loading timetable..." />;
  const d = r?.data || {};

  return (
    <Screen
      eyebrow="Classes"
      title="My Timetable"
      subtitle="Published classroom, blended and online sessions."
    >
      <AlertBox error={error} />
      <Card title="Today's Sessions">
        <Sessions rows={d.today || []} />
      </Card>
      <Card title="Upcoming Sessions">
        <Sessions rows={d.upcoming || []} />
      </Card>
    </Screen>
  );
}

import { View } from "react-native";
import * as A from "../src/api";
import { useLoad } from "../src/useLoad";
import { AlertBox, Badge, Card, Empty, Loading, Row, Screen, Stat, dateZA } from "../src/components";

export default function Attendance() {
  const { data: r, error, loading } = useLoad(A.attendance);
  if (loading) return <Loading text="Loading attendance..." />;

  const d = r?.data || {};
  const s = d.summary || {};
  const rows = d.records || [];

  return (
    <Screen
      eyebrow="Attendance"
      title="My Attendance"
      subtitle="Official attendance only. Draft or unconfirmed attendance is not shown."
    >
      <AlertBox error={error} />
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 10, marginBottom: 13 }}>
        <Stat label="Sessions" value={s.total_sessions ?? 0} />
        <Stat label="Present" value={s.present ?? 0} note={`${s.late ?? 0} late`} />
        <Stat label="Absent" value={s.absent ?? 0} note={`${s.excused ?? 0} excused`} />
        <Stat
          label="Attendance Rate"
          value={s.attendance_rate != null ? `${s.attendance_rate}%` : "—"}
        />
      </View>

      <Card title="Official Attendance History">
        {rows.length ? (
          rows.map((x: any) => (
            <Row
              key={x.attendance_session_id}
              code={x.class_code || x.course_code}
              title={x.session_title || x.class_name || "Training Session"}
              subtitle={`${dateZA(x.session_date)} · ${x.start_time || "—"}–${x.end_time || "—"} · ${x.delivery_mode || "—"}${x.minutes_late != null && x.attendance_status === "Late" ? ` · ${x.minutes_late} min late` : ""}`}
              right={<Badge value={x.attendance_status} />}
            />
          ))
        ) : (
          <Empty
            title="No official attendance published yet"
            text="Confirmed attendance will appear here."
          />
        )}
      </Card>
    </Screen>
  );
}

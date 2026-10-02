import { useEffect, useState } from "react";
import { Linking, View } from "react-native";
import * as A from "../../src/api";
import { useAuth } from "../../src/auth";
import {
  AlertBox,
  Badge,
  Button,
  Card,
  Empty,
  Row,
  Screen,
  Stat,
  dateZA,
  money,
} from "../../src/components";

export default function Dashboard() {
  const auth = useAuth();
  const [data, setData] = useState<any>({});
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.allSettled([
      A.profile(auth.token),
      A.modules(auth.token),
      A.finance(auth.token),
      A.timetable(auth.token),
      A.announcements(auth.token),
    ]).then((r) => {
      setData({
        p: r[0].status === "fulfilled" ? r[0].value.profile : {},
        m: r[1].status === "fulfilled" ? r[1].value.data : {},
        f: r[2].status === "fulfilled" ? r[2].value.data : {},
        t: r[3].status === "fulfilled" ? r[3].value.data : {},
        an:
          r[4].status === "fulfilled"
            ? r[4].value.announcements || []
            : [],
      });
    }).catch((e) => {
      setError(e?.message || "Dashboard could not be loaded.");
    });
  }, [auth.token]);

  const p = data.p || {};
  const m = data.m || {};
  const f = data.f || {};
  const t = data.t || {};

  return (
    <Screen
      eyebrow="Student Dashboard"
      title={`Welcome, ${p.first_name || "Student"}.`}
      subtitle="Your programme, learning progress and student services."
    >
      <AlertBox error={error} />

      <Card title="My Programme">
        <Row
          title={
            m.programme?.course_name ||
            p.course_name ||
            "Programme"
          }
          subtitle={`${m.programme?.course_code || p.course_code || "—"} · NQF ${m.programme?.nqf_level ?? p.nqf_level ?? "—"} · ${p.cycle || "Current intake"}`}
          right={
            <Badge
              value={
                m.programme?.registration_status ||
                p.registration_status ||
                "Registered"
              }
            />
          }
        />
      </Card>

      <View
        style={{
          flexDirection: "row",
          flexWrap: "wrap",
          gap: 10,
          marginBottom: 13,
        }}
      >
        <Stat
          label="Registered Modules"
          value={m.summary?.total_modules ?? "—"}
          note={`${m.summary?.total_registered_credits || 0} credits`}
        />
        <Stat
          label="Upcoming Classes"
          value={t.summary?.upcoming_sessions ?? 0}
          note={`${t.summary?.today_sessions || 0} today`}
        />
        <Stat
          label="Outstanding Balance"
          value={money(f.summary?.outstanding_balance)}
        />
        <Stat
          label="Announcements"
          value={(data.an || []).length}
        />
      </View>

      <Card title="Next Classes">
        {t.upcoming?.length ? (
          t.upcoming.slice(0, 4).map((s: any) => (
            <View key={s.session_id}>
              <Row
                title={s.session_title}
                subtitle={`${dateZA(s.session_date)} · ${s.start_time}–${s.end_time} · ${s.delivery_mode}`}
              />
              {s.can_join_online && !!s.join_online_url && (
                <View style={{ marginBottom: 10 }}>
                  <Button
                    title="Join Online Class"
                    onPress={() =>
                      void Linking.openURL(s.join_online_url)
                    }
                    secondary
                  />
                </View>
              )}
            </View>
          ))
        ) : (
          <Empty
            title="No upcoming classes"
            text="Published timetable sessions will appear here."
          />
        )}
      </Card>

      <Card title="Announcements">
        {data.an?.length ? (
          data.an.slice(0, 5).map((x: any) => (
            <Row
              key={x.id}
              title={x.title || x.subject}
              subtitle={dateZA(x.published_at || x.created_at)}
            />
          ))
        ) : (
          <Empty title="No announcements" />
        )}
      </Card>
    </Screen>
  );
}

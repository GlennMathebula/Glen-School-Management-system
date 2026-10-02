import { router } from "expo-router";
import { Card, Row, Screen } from "../../src/components";

const items = [
  ["My Modules", "Registered KM, PM and WM modules.", "/modules"],
  ["Module Results", "Published module marks and results.", "/results"],
  ["FISA / EISA", "Summative assessment progress and outcomes.", "/assessments"],
  ["Attendance", "Your official attendance record.", "/attendance"],
  ["Timetable", "Published classes and online sessions.", "/timetable"],
  ["Learning Resources", "Published learning material.", "/resources"],
];

export default function Learning() {
  return (
    <Screen
      eyebrow="Academic"
      title="My Learning"
      subtitle="Everything connected to your programme delivery and assessment."
    >
      <Card>
        {items.map(([title, subtitle, href]) => (
          <Row
            key={href}
            title={title}
            subtitle={subtitle}
            right={"›"}
            onPress={() => router.push(href as any)}
          />
        ))}
      </Card>
    </Screen>
  );
}

import { router } from "expo-router";
import { useAuth } from "../../src/auth";
import { Button, Card, Row, Screen } from "../../src/components";

const items = [
  ["Student Card", "Digital card, QR, photo and replacement request.", "/card"],
  ["Completion Documents", "Completion and graduation letters.", "/completion"],
  ["Messages", "Announcements and student communication.", "/messages"],
  ["Support", "Create and track support requests.", "/support"],
  ["My Account", "Profile, contact details and security.", "/account"],
];

export default function More() {
  const auth = useAuth();

  return (
    <Screen
      eyebrow="Student Services"
      title="More"
      subtitle="Identity, communication, completion and account services."
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

      <Button
        title="Sign Out"
        secondary
        onPress={() => {
          void auth.logout();
          router.replace("/login");
        }}
      />
    </Screen>
  );
}

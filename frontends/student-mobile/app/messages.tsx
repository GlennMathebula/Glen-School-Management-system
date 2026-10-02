import { useEffect, useState } from "react";
import * as A from "../src/api";
import { useAuth } from "../src/auth";
import { AlertBox, Button, Card, Empty, Field, Loading, Row, Screen, dateZA } from "../src/components";

export default function Messages() {
  const auth = useAuth();
  const [announcements, setAnnouncements] = useState<any[]>([]);
  const [threads, setThreads] = useState<any[]>([]);
  const [subject, setSubject] = useState("");
  const [messageText, setMessageText] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    const r = await Promise.allSettled([
      A.announcements(auth.token),
      A.messages(auth.token),
    ]);

    if (r[0].status === "fulfilled") {
      setAnnouncements(r[0].value.announcements || []);
    }

    if (r[1].status === "fulfilled") {
      setThreads(r[1].value.threads || []);
    }

    setLoading(false);
  }

  useEffect(() => {
    void load();
  }, [auth.token]);

  async function send() {
    if (!subject.trim() || !messageText.trim()) {
      setError("Enter a subject and message.");
      return;
    }

    setError("");
    setMessage("");

    try {
      await A.newMessage(
        {
          category: "General",
          subject: subject.trim(),
          message: messageText.trim(),
        },
        auth.token
      );
      setSubject("");
      setMessageText("");
      setMessage("Message sent.");
      await load();
    } catch (e: any) {
      setError(e?.message || "Message could not be sent.");
    }
  }

  if (loading) return <Loading text="Loading messages..." />;

  return (
    <Screen
      eyebrow="Communication"
      title="Messages & Announcements"
      subtitle="Read notices and contact Glen Moniques."
    >
      <AlertBox error={error} message={message} />

      <Card title="Announcements">
        {announcements.length ? (
          announcements.map((x) => (
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

      <Card title="Send a Message">
        <Field
          label="Subject"
          value={subject}
          onChangeText={setSubject}
        />
        <Field
          label="Message"
          multiline
          value={messageText}
          onChangeText={setMessageText}
        />
        <Button title="Send Message" onPress={() => void send()} />
      </Card>

      <Card title="My Message Threads">
        {threads.length ? (
          threads.map((x) => (
            <Row
              key={x.id}
              title={x.subject}
              subtitle={`${x.category || "General"} · ${dateZA(x.updated_at || x.created_at)}`}
              right={x.status}
            />
          ))
        ) : (
          <Empty title="No message threads yet" />
        )}
      </Card>
    </Screen>
  );
}

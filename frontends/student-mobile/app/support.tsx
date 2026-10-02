import { useEffect, useState } from "react";
import * as A from "../src/api";
import { useAuth } from "../src/auth";
import { AlertBox, Badge, Button, Card, Empty, Field, Loading, Row, Screen, dateZA } from "../src/components";

export default function Support() {
  const auth = useAuth();
  const [tickets, setTickets] = useState<any[]>([]);
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const response = await A.support(auth.token);
      setTickets(response?.tickets || []);
    } catch (e: any) {
      setError(e?.message || "Support tickets could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [auth.token]);

  async function send() {
    if (!subject.trim() || !description.trim()) {
      setError("Enter a subject and description.");
      return;
    }

    setError("");
    setMessage("");

    try {
      await A.newSupport(
        {
          category: "MobileApp",
          priority: "Normal",
          subject: subject.trim(),
          description: description.trim(),
        },
        auth.token
      );
      setSubject("");
      setDescription("");
      setMessage("Support ticket created.");
      await load();
    } catch (e: any) {
      setError(e?.message || "Ticket could not be created.");
    }
  }

  if (loading) return <Loading text="Loading support..." />;

  return (
    <Screen
      eyebrow="Help"
      title="Student Support"
      subtitle="Create and track student-service and technical support requests."
    >
      <AlertBox error={error} message={message} />

      <Card title="My Support Tickets">
        {tickets.length ? (
          tickets.map((x) => (
            <Row
              key={x.id}
              code={x.ticket_number}
              title={x.subject}
              subtitle={`${x.category} · ${x.priority} · ${dateZA(x.created_at)}`}
              right={<Badge value={x.status} />}
            />
          ))
        ) : (
          <Empty title="No support tickets" />
        )}
      </Card>

      <Card title="Create Support Ticket">
        <Field
          label="Subject"
          value={subject}
          onChangeText={setSubject}
        />
        <Field
          label="Description"
          multiline
          value={description}
          onChangeText={setDescription}
        />
        <Button
          title="Create Ticket"
          onPress={() => void send()}
        />
      </Card>
    </Screen>
  );
}

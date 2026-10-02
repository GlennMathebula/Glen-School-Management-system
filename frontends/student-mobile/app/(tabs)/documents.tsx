import { useEffect, useState } from "react";
import * as DocumentPicker from "expo-document-picker";
import * as A from "../../src/api";
import { useAuth } from "../../src/auth";
import { AlertBox, Badge, Button, Card, Empty, Loading, Row, Screen } from "../../src/components";

export default function Documents() {
  const auth = useAuth();
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const response = await A.documents(auth.token);
      setData(response?.data || {});
    } catch (e: any) {
      setError(e?.message || "Documents could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [auth.token]);

  async function upload(request: any) {
    const pick = await DocumentPicker.getDocumentAsync({
      type: ["application/pdf", "image/jpeg", "image/png"],
      copyToCacheDirectory: true,
      multiple: false,
    });

    if (pick.canceled || !pick.assets?.[0]) return;

    setBusy(true);
    setError("");
    setMessage("");

    try {
      await A.uploadDocument(
        request.request_id,
        pick.assets[0],
        auth.token
      );
      setMessage("Document uploaded successfully.");
      await load();
    } catch (e: any) {
      setError(e?.message || "Upload failed.");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <Loading text="Loading documents..." />;

  const outstanding = data?.outstanding_requests || [];
  const docs = [
    ...(data?.documents?.pending || []),
    ...(data?.documents?.approved || []),
    ...(data?.documents?.rejected || []),
  ];

  return (
    <Screen
      eyebrow="Records"
      title="Document Centre"
      subtitle="Upload requested documents and monitor review status."
    >
      <AlertBox error={error} message={message} />

      <Card title="Documents Required From You">
        {outstanding.length ? (
          outstanding.map((x: any) => (
            <Row
              key={x.request_id}
              code={x.document_type}
              title={x.document_label}
              subtitle={x.instructions || x.reason || "Requested document"}
              right={
                <Button
                  title={busy ? "..." : "Upload"}
                  disabled={busy}
                  onPress={() => void upload(x)}
                />
              }
            />
          ))
        ) : (
          <Empty title="No outstanding document requests" />
        )}
      </Card>

      <Card title="My Current Documents">
        {docs.length ? (
          docs.map((x: any) => (
            <Row
              key={x.document_id}
              title={x.document_label}
              subtitle={x.original_filename}
              right={<Badge value={x.review_status} />}
            />
          ))
        ) : (
          <Empty title="No current documents" />
        )}
      </Card>
    </Screen>
  );
}

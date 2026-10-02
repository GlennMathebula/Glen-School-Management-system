import { Linking } from "react-native";
import * as A from "../src/api";
import { useAuth } from "../src/auth";
import { useLoad } from "../src/useLoad";
import { AlertBox, Button, Card, Empty, Loading, Row, Screen } from "../src/components";
import { useState } from "react";

export default function Resources() {
  const auth = useAuth();
  const { data: r, error, loading } = useLoad(A.resources);
  const [actionError, setActionError] = useState("");

  if (loading) return <Loading text="Loading resources..." />;

  const rows = Array.isArray(r)
    ? r
    : r?.resources || r?.data?.resources || (Array.isArray(r?.data) ? r.data : []);

  async function openResource(x: any) {
    setActionError("");
    try {
      const id = x.resource_id || x.id;
      const response = id ? await A.resource(id, auth.token) : x;
      const d = response?.resource || response?.data || response || x;
      const url =
        d?.signed_url ||
        d?.download_url ||
        d?.file_url ||
        d?.url;

      if (url) {
        await Linking.openURL(url);
      } else {
        throw new Error(
          "This resource has no mobile download URL yet."
        );
      }
    } catch (e: any) {
      setActionError(e?.message || "Resource could not be opened.");
    }
  }

  return (
    <Screen
      eyebrow="Learning"
      title="Learning Resources"
      subtitle="Published learning material available to your classes."
    >
      <AlertBox error={error || actionError} />
      <Card title="Published Resources">
        {rows.length ? (
          rows.map((x: any, i: number) => (
            <Row
              key={x.resource_id || x.id || i}
              code={x.module_code || x.resource_type || "RESOURCE"}
              title={x.title || x.resource_title || x.name || x.file_name || "Learning Resource"}
              subtitle={x.description || x.original_filename || x.resource_type}
              right={
                <Button
                  title="Open"
                  onPress={() => void openResource(x)}
                  secondary
                />
              }
            />
          ))
        ) : (
          <Empty
            title="No learning resources published"
            text="Published class resources will appear here."
          />
        )}
      </Card>
    </Screen>
  );
}

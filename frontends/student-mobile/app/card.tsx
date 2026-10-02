import { useEffect, useState } from "react";
import {
  Image,
  StyleSheet,
  Text,
  View,
} from "react-native";
import * as ImagePicker from "expo-image-picker";
import * as A from "../src/api";
import { API_BASE } from "../src/api";
import { useAuth } from "../src/auth";
import { downloadProtected } from "../src/files";
import {
  AlertBox,
  Badge,
  Button,
  Card,
  Field,
  Info,
  Loading,
  Screen,
} from "../src/components";
import { C } from "../src/theme";

export default function StudentCard() {
  const auth = useAuth();
  const [data, setData] = useState<any>(null);
  const [reason, setReason] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const response = await A.card(auth.token);
      setData(response?.data || null);
    } catch (e: any) {
      setError(e?.message || "Student card could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [auth.token]);

  async function pickPhoto() {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ["images"],
      allowsEditing: true,
      quality: 0.9,
    });

    if (result.canceled || !result.assets?.[0]) return;

    setError("");
    setMessage("");

    try {
      const response = await A.uploadAvatar(
        result.assets[0],
        auth.token
      );
      setMessage(response?.message || "Photo uploaded.");
      await load();
    } catch (e: any) {
      setError(e?.message || "Photo upload failed.");
    }
  }

  async function requestReplacement() {
    if (reason.trim().length < 5) {
      setError("Give a reason of at least 5 characters.");
      return;
    }

    try {
      const response = await A.requestAvatarReplacement(
        reason.trim(),
        auth.token
      );
      setReason("");
      setMessage(
        response?.message || "Replacement request submitted."
      );
      await load();
    } catch (e: any) {
      setError(e?.message || "Replacement request failed.");
    }
  }

  if (loading) return <Loading text="Loading student card..." />;

  const avatarUri = data?.avatar?.available
    ? `${API_BASE}/api/student/card/avatar`
    : "";
  const qrUri = data?.qr_url
    ? `${API_BASE}${data.qr_url}`
    : `${API_BASE}/api/student/card/qr`;

  return (
    <Screen
      eyebrow="Identity"
      title="My Student Card"
      subtitle="Your Glen Moniques student identity card and QR verification."
    >
      <AlertBox error={error} message={message} />

      {!!data && (
        <>
          <View style={s.idCard}>
            <Text style={s.brand}>GLEN MONIQUES</Text>
            <Text style={s.label}>STUDENT CARD</Text>

            <View style={s.body}>
              <View style={s.photo}>
                {avatarUri ? (
                  <Image
                    source={{
                      uri: avatarUri,
                      headers: {
                        Authorization: `Bearer ${auth.token}`,
                      },
                    }}
                    style={s.photoImg}
                  />
                ) : (
                  <Text style={s.photoText}>PHOTO</Text>
                )}
              </View>

              <View style={{ flex: 1 }}>
                <Text style={s.name}>{data.full_name}</Text>
                <Text style={s.number}>{data.student_number}</Text>
                <Text style={s.course}>
                  {data.course?.course_name}
                </Text>
                <Text style={s.small}>
                  {data.course?.course_code} · NQF{" "}
                  {data.course?.nqf_level}
                </Text>
              </View>
            </View>

            <View style={s.footer}>
              <Text style={s.small}>
                {data.registration?.cycle}
              </Text>
              <Badge value={data.card?.status} />
            </View>
          </View>

          <Card title="QR Verification">
            <Image
              source={{
                uri: qrUri,
                headers: {
                  Authorization: `Bearer ${auth.token}`,
                },
              }}
              style={s.qr}
              resizeMode="contain"
            />
          </Card>

          <Card title="Card & Photo">
            <Info label="Card Status" value={data.card?.status} />
            <Info
              label="Photo Permission"
              value={data.avatar?.upload_permission}
            />

            {data.avatar?.replacement_requested && (
              <>
                <Info
                  label="Replacement Request"
                  value="Awaiting Administration"
                />
                <Info
                  label="Reason"
                  value={data.avatar?.replacement_reason}
                />
              </>
            )}

            {data.avatar?.can_upload && (
              <>
                <View style={{ height: 12 }} />
                <Button
                  title="Choose & Upload Card Photo"
                  onPress={() => void pickPhoto()}
                />
              </>
            )}

            {data.avatar?.can_request_replacement && (
              <>
                <View style={{ height: 14 }} />
                <Field
                  label="Reason for replacing your photo"
                  multiline
                  value={reason}
                  onChangeText={setReason}
                  placeholder="Explain why the current photo must be replaced."
                />
                <Button
                  title="Request Photo Replacement"
                  secondary
                  onPress={() => void requestReplacement()}
                />
              </>
            )}
          </Card>

          <Button
            title="Download / Share Student Card PDF"
            onPress={() =>
              void downloadProtected(
                "/api/student/card/pdf",
                auth.token,
                `Student_Card_${auth.meta?.student_number}.pdf`
              )
            }
          />
        </>
      )}
    </Screen>
  );
}

const s = StyleSheet.create({
  idCard: {
    backgroundColor: C.navy,
    borderRadius: 16,
    padding: 18,
    marginBottom: 13,
  },
  brand: {
    color: "#FFFFFF",
    fontWeight: "900",
    fontSize: 15,
  },
  label: {
    color: C.gold,
    fontWeight: "900",
    fontSize: 10,
    marginTop: 2,
  },
  body: {
    flexDirection: "row",
    gap: 14,
    alignItems: "center",
    marginTop: 18,
  },
  photo: {
    width: 90,
    height: 110,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#FFFFFF30",
    backgroundColor: "#FFFFFF12",
    alignItems: "center",
    justifyContent: "center",
    overflow: "hidden",
  },
  photoImg: {
    width: "100%",
    height: "100%",
  },
  photoText: {
    color: "#FFFFFF99",
    fontSize: 10,
  },
  name: {
    color: "#FFFFFF",
    fontSize: 19,
    fontWeight: "900",
  },
  number: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "800",
    marginTop: 3,
  },
  course: {
    color: C.gold,
    fontSize: 12,
    fontWeight: "800",
    marginTop: 10,
  },
  small: {
    color: "#FFFFFFAA",
    fontSize: 10,
    marginTop: 3,
  },
  footer: {
    borderTopWidth: 1,
    borderTopColor: "#FFFFFF20",
    marginTop: 16,
    paddingTop: 12,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  qr: {
    width: 180,
    height: 180,
    alignSelf: "center",
  },
});

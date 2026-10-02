import { useState } from "react";
import { router } from "expo-router";
import {
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  View,
} from "react-native";
import * as A from "../src/api";
import { useAuth } from "../src/auth";
import { AlertBox, Button, Field } from "../src/components";
import { C } from "../src/theme";

export default function Onboarding() {
  const auth = useAuth();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [pinPassword, setPinPassword] = useState("");
  const [pin, setPin] = useState("");
  const [pinConfirm, setPinConfirm] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  const needPassword = !!auth.meta?.must_change_password;

  async function changePassword() {
    if (next !== confirm) {
      setError("New passwords do not match.");
      return;
    }

    setBusy(true);
    setError("");
    setMessage("");

    try {
      const response = await A.changePassword({
        student_number: auth.meta?.student_number,
        current_password: current,
        new_password: next,
      });
      const result = response?.result || response;

      await auth.update(result.access_token, {
        login_method: "password_pending_pin",
        must_change_password: false,
        pin_created: !!result.pin_created,
      });

      setPinPassword(next);
      setMessage("Password changed. Now create your PIN.");
    } catch (e: any) {
      setError(e?.message || "Could not change password.");
    } finally {
      setBusy(false);
    }
  }

  async function createPin() {
    if (pin !== pinConfirm) {
      setError("PIN entries do not match.");
      return;
    }

    if (!/^\d{5}$/.test(pin)) {
      setError("PIN must contain exactly 5 digits.");
      return;
    }

    setBusy(true);
    setError("");
    setMessage("");

    try {
      await A.setupPin({
        student_number: auth.meta?.student_number,
        password: pinPassword,
        pin,
      });

      await auth.update(auth.token, {
        pin_created: true,
        must_change_password: false,
        login_method: "password_pending_pin",
      });

      await auth.loginPin(
        auth.meta?.student_number || "",
        pin
      );

      router.replace("/(tabs)/dashboard");
    } catch (e: any) {
      setError(e?.message || "Could not create PIN.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={s.page}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <View style={s.card}>
        <Text style={s.eyebrow}>FIRST-TIME SETUP</Text>
        <Text style={s.title}>Secure Your Account</Text>
        <Text style={s.student}>
          {auth.meta?.student_number}
        </Text>

        <AlertBox error={error} message={message} />

        {needPassword ? (
          <>
            <Text style={s.note}>
              Your new password must meet the security rules enforced
              by the Glen Moniques backend.
            </Text>
            <Field
              label="Temporary / Current Password"
              secureTextEntry
              value={current}
              onChangeText={setCurrent}
            />
            <Field
              label="New Password"
              secureTextEntry
              value={next}
              onChangeText={setNext}
            />
            <Field
              label="Confirm Password"
              secureTextEntry
              value={confirm}
              onChangeText={setConfirm}
            />
            <Button
              title={busy ? "Saving..." : "Change Password"}
              onPress={changePassword}
              disabled={busy}
            />
          </>
        ) : (
          <>
            <Text style={s.note}>
              Create the same secure 5-digit PIN you will use as the
              second sign-in step.
            </Text>
            <Field
              label="Current Password"
              secureTextEntry
              value={pinPassword}
              onChangeText={setPinPassword}
            />
            <Field
              label="5-Digit PIN"
              secureTextEntry
              keyboardType="number-pad"
              maxLength={5}
              value={pin}
              onChangeText={(v) => setPin(v.replace(/\D/g, ""))}
            />
            <Field
              label="Confirm PIN"
              secureTextEntry
              keyboardType="number-pad"
              maxLength={5}
              value={pinConfirm}
              onChangeText={(v) =>
                setPinConfirm(v.replace(/\D/g, ""))
              }
            />
            <Button
              title={busy ? "Saving..." : "Create PIN & Enter App"}
              onPress={createPin}
              disabled={busy}
            />
          </>
        )}

        <View style={{ height: 10 }} />
        <Button
          title="Sign out"
          onPress={() => {
            void auth.logout();
            router.replace("/login");
          }}
          secondary
        />
      </View>
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  page: {
    flex: 1,
    justifyContent: "center",
    padding: 18,
    backgroundColor: C.bg,
  },
  card: {
    backgroundColor: "#FFFFFF",
    borderColor: C.line,
    borderWidth: 1,
    borderRadius: 16,
    padding: 20,
  },
  eyebrow: {
    color: "#95670B",
    fontSize: 10,
    fontWeight: "900",
    letterSpacing: 1.2,
  },
  title: {
    color: C.navy,
    fontSize: 28,
    fontWeight: "900",
    marginTop: 5,
  },
  student: {
    color: C.muted,
    marginTop: 4,
    marginBottom: 16,
  },
  note: {
    color: "#587691",
    backgroundColor: "#EDF6FB",
    padding: 11,
    borderRadius: 9,
    fontSize: 12,
    lineHeight: 18,
    marginBottom: 13,
  },
});

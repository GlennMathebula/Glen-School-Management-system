import { useState } from "react";
import {
  Image,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { router } from "expo-router";
import { AlertBox, Button, Field } from "../src/components";
import { useAuth } from "../src/auth";
import { C, shadow } from "../src/theme";

export default function Login() {
  const auth = useAuth();
  const [studentNumber, setStudentNumber] = useState(
    auth.meta?.student_number || ""
  );
  const [password, setPassword] = useState("");
  const [pin, setPin] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const step = auth.needsPin ? "pin" : "password";

  async function passwordStep() {
    if (!/^\d{8}$/.test(studentNumber)) {
      setError("Enter your 8-digit student number.");
      return;
    }
    if (!password) {
      setError("Enter your password.");
      return;
    }

    setBusy(true);
    setError("");

    try {
      const result = await auth.loginPassword(
        studentNumber,
        password
      );

      if (
        result.must_change_password ||
        result.pin_created === false
      ) {
        router.replace("/onboarding");
        return;
      }
    } catch (e: any) {
      setError(e?.message || "Sign-in failed.");
    } finally {
      setBusy(false);
    }
  }

  async function pinStep() {
    if (!/^\d{5}$/.test(pin)) {
      setError("Enter your 5-digit PIN.");
      return;
    }

    setBusy(true);
    setError("");

    try {
      await auth.loginPin(
        auth.meta?.student_number || studentNumber,
        pin
      );
      router.replace("/(tabs)/dashboard");
    } catch (e: any) {
      setError(e?.message || "PIN verification failed.");
    } finally {
      setBusy(false);
    }
  }

  async function restart() {
    await auth.logout();
    setStudentNumber("");
    setPassword("");
    setPin("");
    setError("");
  }

  return (
    <KeyboardAvoidingView
      style={s.page}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <View style={s.hero}>
        <Image
          source={require("../assets/images/glen-moniques-logo.png")}
          style={s.logo}
          resizeMode="contain"
        />
        <Text style={s.brand}>GLEN MONIQUES</Text>
        <Text style={s.heroTitle}>Student App</Text>
        <Text style={s.heroText}>
          Your programme, learning, attendance, finance and
          student services in one secure mobile app.
        </Text>
      </View>

      <View style={s.card}>
        <Text style={s.eyebrow}>
          {step === "password" ? "STEP 1 OF 2" : "STEP 2 OF 2"}
        </Text>
        <Text style={s.title}>
          {step === "password"
            ? "Student Sign In"
            : "Enter Your PIN"}
        </Text>

        <AlertBox error={error} />

        {step === "password" ? (
          <>
            <Field
              label="Student Number"
              keyboardType="number-pad"
              maxLength={8}
              value={studentNumber}
              onChangeText={(v) =>
                setStudentNumber(v.replace(/\D/g, ""))
              }
              placeholder="8-digit student number"
            />
            <Field
              label="Password"
              secureTextEntry
              value={password}
              onChangeText={setPassword}
              placeholder="Password"
            />
            <Button
              title={busy ? "Verifying..." : "Continue to PIN"}
              onPress={passwordStep}
              disabled={busy}
            />
          </>
        ) : (
          <>
            <Text style={s.hint}>
              Password verified for student{" "}
              {auth.meta?.student_number}.
            </Text>
            <Field
              label="5-Digit PIN"
              secureTextEntry
              keyboardType="number-pad"
              maxLength={5}
              value={pin}
              onChangeText={(v) =>
                setPin(v.replace(/\D/g, ""))
              }
              placeholder="PIN"
            />
            <Button
              title={busy ? "Verifying PIN..." : "Enter Student App"}
              onPress={pinStep}
              disabled={busy}
            />
            <View style={{ height: 10 }} />
            <Button
              title="Use a different student number"
              onPress={restart}
              secondary
            />
          </>
        )}
      </View>
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  page: {
    flex: 1,
    backgroundColor: C.bg,
    justifyContent: "center",
  },
  hero: {
    backgroundColor: C.navy,
    paddingHorizontal: 24,
    paddingTop: 56,
    paddingBottom: 28,
  },
  logo: {
    width: 62,
    height: 62,
    backgroundColor: "#FFFFFF",
    borderRadius: 13,
    marginBottom: 14,
  },
  brand: {
    color: C.gold,
    fontSize: 11,
    fontWeight: "900",
    letterSpacing: 1.5,
  },
  heroTitle: {
    color: "#FFFFFF",
    fontSize: 36,
    fontWeight: "900",
    marginTop: 4,
  },
  heroText: {
    color: "#FFFFFFAA",
    marginTop: 8,
    fontSize: 13,
    lineHeight: 20,
  },
  card: {
    margin: 18,
    marginTop: -12,
    backgroundColor: "#FFFFFF",
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: C.line,
    ...shadow,
  },
  eyebrow: {
    color: "#95670B",
    fontSize: 10,
    fontWeight: "900",
    letterSpacing: 1.2,
  },
  title: {
    color: C.navy,
    fontSize: 27,
    fontWeight: "900",
    marginVertical: 9,
  },
  hint: {
    color: C.muted,
    fontSize: 12,
    lineHeight: 18,
    marginBottom: 12,
  },
});

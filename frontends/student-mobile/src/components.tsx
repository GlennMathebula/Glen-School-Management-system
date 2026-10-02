import React from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleProp,
  StyleSheet,
  Text,
  TextInput,
  TextInputProps,
  View,
  ViewStyle,
} from "react-native";
import { C, shadow } from "./theme";

export function Screen({
  children,
  title,
  eyebrow,
  subtitle,
  scroll = true,
}: {
  children: React.ReactNode;
  title: string;
  eyebrow?: string;
  subtitle?: string;
  scroll?: boolean;
}) {
  const content = (
    <View style={styles.screenInner}>
      {!!eyebrow && <Text style={styles.eyebrow}>{eyebrow}</Text>}
      <Text style={styles.pageTitle}>{title}</Text>
      {!!subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
      <View style={styles.gap} />
      {children}
    </View>
  );

  if (!scroll) return <View style={styles.screen}>{content}</View>;

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={{ paddingBottom: 48 }}
      keyboardShouldPersistTaps="handled"
    >
      {content}
    </ScrollView>
  );
}

export function Card({
  children,
  title,
  style,
}: {
  children: React.ReactNode;
  title?: string;
  style?: StyleProp<ViewStyle>;
}) {
  return (
    <View style={[styles.card, style]}>
      {!!title && <Text style={styles.cardTitle}>{title}</Text>}
      {children}
    </View>
  );
}

export function Stat({
  label,
  value,
  note,
}: {
  label: string;
  value: React.ReactNode;
  note?: string;
}) {
  return (
    <View style={styles.stat}>
      <Text style={styles.statLabel}>{label}</Text>
      <Text style={styles.statValue}>{value ?? "—"}</Text>
      {!!note && <Text style={styles.statNote}>{note}</Text>}
    </View>
  );
}

export function Badge({ value }: { value?: string | null }) {
  const v = String(value || "—");
  const key = v.toLowerCase();
  const good = [
    "active",
    "registered",
    "present",
    "pass",
    "published",
    "completed",
    "approved",
  ].some((x) => key.includes(x));
  const bad = ["absent", "fail", "rejected"].some((x) =>
    key.includes(x)
  );

  return (
    <View
      style={[
        styles.badge,
        good && styles.badgeGood,
        bad && styles.badgeBad,
      ]}
    >
      <Text
        style={[
          styles.badgeText,
          good && styles.badgeTextGood,
          bad && styles.badgeTextBad,
        ]}
      >
        {v}
      </Text>
    </View>
  );
}

export function Row({
  title,
  subtitle,
  code,
  right,
  onPress,
}: {
  title: string;
  subtitle?: string;
  code?: string;
  right?: React.ReactNode;
  onPress?: () => void;
}) {
  const content = (
    <View style={styles.row}>
      <View style={{ flex: 1, gap: 3 }}>
        {!!code && <Text style={styles.code}>{code}</Text>}
        <Text style={styles.rowTitle}>{title}</Text>
        {!!subtitle && <Text style={styles.rowSub}>{subtitle}</Text>}
      </View>
      {!!right && <View>{right}</View>}
    </View>
  );

  return onPress ? (
    <Pressable onPress={onPress}>{content}</Pressable>
  ) : (
    content
  );
}

export function Button({
  title,
  onPress,
  secondary = false,
  disabled = false,
}: {
  title: string;
  onPress: () => void;
  secondary?: boolean;
  disabled?: boolean;
}) {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      style={({ pressed }) => [
        styles.button,
        secondary && styles.buttonSecondary,
        (pressed || disabled) && { opacity: 0.65 },
      ]}
    >
      <Text
        style={[
          styles.buttonText,
          secondary && styles.buttonTextSecondary,
        ]}
      >
        {title}
      </Text>
    </Pressable>
  );
}

export function Field({
  label,
  multiline,
  ...props
}: TextInputProps & { label: string }) {
  return (
    <View style={{ gap: 6, marginBottom: 13 }}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <TextInput
        {...props}
        multiline={multiline}
        style={[
          styles.input,
          multiline && {
            minHeight: 96,
            textAlignVertical: "top",
          },
        ]}
        placeholderTextColor="#9BA7B3"
      />
    </View>
  );
}

export function AlertBox({
  error,
  message,
}: {
  error?: string;
  message?: string;
}) {
  if (!error && !message) return null;
  return (
    <View
      style={[
        styles.alert,
        error ? styles.alertError : styles.alertOk,
      ]}
    >
      <Text
        style={[
          styles.alertText,
          error ? styles.alertTextError : styles.alertTextOk,
        ]}
      >
        {error || message}
      </Text>
    </View>
  );
}

export function Loading({ text = "Loading..." }: { text?: string }) {
  return (
    <View style={styles.loading}>
      <ActivityIndicator color={C.gold} size="large" />
      <Text style={styles.muted}>{text}</Text>
    </View>
  );
}

export function Empty({
  title,
  text,
}: {
  title: string;
  text?: string;
}) {
  return (
    <View style={styles.empty}>
      <Text style={styles.emptyDot}>•</Text>
      <Text style={styles.rowTitle}>{title}</Text>
      {!!text && <Text style={styles.muted}>{text}</Text>}
    </View>
  );
}

export function Info({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) {
  return (
    <View style={styles.info}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={styles.infoValue}>{value ?? "—"}</Text>
    </View>
  );
}

export function dateZA(value: any) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);
  return new Intl.DateTimeFormat("en-ZA", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(d);
}

export function money(value: any) {
  return new Intl.NumberFormat("en-ZA", {
    style: "currency",
    currency: "ZAR",
  }).format(Number(value || 0));
}

export const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: C.bg,
  },
  screenInner: {
    padding: 18,
    paddingTop: 20,
  },
  eyebrow: {
    color: "#95670B",
    fontSize: 11,
    fontWeight: "900",
    letterSpacing: 1.3,
    textTransform: "uppercase",
  },
  pageTitle: {
    color: C.navy,
    fontSize: 30,
    fontWeight: "900",
    letterSpacing: -0.8,
    marginTop: 4,
  },
  subtitle: {
    color: C.muted,
    fontSize: 13,
    lineHeight: 20,
    marginTop: 5,
  },
  gap: {
    height: 18,
  },
  card: {
    backgroundColor: C.card,
    borderColor: C.line,
    borderWidth: 1,
    borderRadius: 14,
    padding: 15,
    marginBottom: 13,
    ...shadow,
  },
  cardTitle: {
    color: C.navy,
    fontSize: 15,
    fontWeight: "900",
    marginBottom: 10,
  },
  stat: {
    backgroundColor: C.card,
    borderColor: C.line,
    borderWidth: 1,
    borderRadius: 12,
    padding: 14,
    flex: 1,
    minWidth: 145,
  },
  statLabel: {
    color: C.muted,
    fontSize: 11,
  },
  statValue: {
    color: C.navy,
    fontSize: 20,
    fontWeight: "900",
    marginTop: 4,
  },
  statNote: {
    color: C.muted,
    fontSize: 10,
    marginTop: 4,
  },
  badge: {
    paddingHorizontal: 9,
    paddingVertical: 5,
    borderRadius: 999,
    backgroundColor: "#EDF1F4",
  },
  badgeText: {
    fontSize: 10,
    fontWeight: "900",
    color: "#4E6174",
  },
  badgeGood: { backgroundColor: "#E5F6ED" },
  badgeBad: { backgroundColor: "#FDEAEA" },
  badgeTextGood: { color: "#12613F" },
  badgeTextBad: { color: "#992F2F" },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#EDF0F2",
  },
  rowTitle: {
    color: "#294159",
    fontSize: 13,
    fontWeight: "800",
  },
  rowSub: {
    color: C.muted,
    fontSize: 11,
    lineHeight: 17,
  },
  code: {
    color: "#95670B",
    fontSize: 10,
    fontWeight: "900",
  },
  button: {
    minHeight: 44,
    borderRadius: 9,
    paddingHorizontal: 14,
    paddingVertical: 11,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: C.gold,
  },
  buttonSecondary: {
    backgroundColor: C.card,
    borderWidth: 1,
    borderColor: C.line,
  },
  buttonText: {
    color: C.navy,
    fontWeight: "900",
    fontSize: 13,
  },
  buttonTextSecondary: {
    color: C.navy,
  },
  fieldLabel: {
    color: "#294159",
    fontSize: 12,
    fontWeight: "800",
  },
  input: {
    minHeight: 46,
    borderWidth: 1.5,
    borderColor: "#D4DDE5",
    backgroundColor: "#FBFCFD",
    borderRadius: 9,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: C.text,
    fontSize: 14,
  },
  alert: {
    borderRadius: 9,
    padding: 11,
    marginBottom: 12,
    borderWidth: 1,
  },
  alertError: {
    backgroundColor: "#FFF0F0",
    borderColor: "#EFC4C4",
  },
  alertOk: {
    backgroundColor: "#EAF8F1",
    borderColor: "#BDE1CD",
  },
  alertText: {
    fontSize: 12,
    lineHeight: 18,
  },
  alertTextError: { color: "#982E2E" },
  alertTextOk: { color: "#126141" },
  loading: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    backgroundColor: C.bg,
  },
  muted: {
    color: C.muted,
    fontSize: 12,
    lineHeight: 18,
  },
  empty: {
    alignItems: "center",
    paddingVertical: 24,
    gap: 5,
  },
  emptyDot: {
    color: C.gold,
    fontSize: 30,
  },
  info: {
    flexDirection: "row",
    paddingVertical: 9,
    borderBottomWidth: 1,
    borderBottomColor: "#EDF0F2",
    gap: 10,
  },
  infoLabel: {
    width: "42%",
    color: C.muted,
    fontSize: 12,
  },
  infoValue: {
    flex: 1,
    color: "#294159",
    fontSize: 12,
    fontWeight: "700",
  },
});

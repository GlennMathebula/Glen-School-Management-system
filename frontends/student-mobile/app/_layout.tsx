import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { AuthProvider } from "../src/auth";
import { C } from "../src/theme";

export default function RootLayout() {
  return (
    <AuthProvider>
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: C.navy },
          headerTintColor: "#FFFFFF",
          headerTitleStyle: { fontWeight: "800" },
          contentStyle: { backgroundColor: C.bg },
        }}
      >
        <Stack.Screen name="index" options={{ headerShown: false }} />
        <Stack.Screen name="login" options={{ headerShown: false }} />
        <Stack.Screen name="onboarding" options={{ headerShown: false }} />
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="modules" options={{ title: "My Modules" }} />
        <Stack.Screen name="results" options={{ title: "Module Results" }} />
        <Stack.Screen name="assessments" options={{ title: "FISA / EISA" }} />
        <Stack.Screen name="attendance" options={{ title: "Attendance" }} />
        <Stack.Screen name="timetable" options={{ title: "Timetable" }} />
        <Stack.Screen name="resources" options={{ title: "Learning Resources" }} />
        <Stack.Screen name="card" options={{ title: "Student Card" }} />
        <Stack.Screen name="completion" options={{ title: "Completion Documents" }} />
        <Stack.Screen name="messages" options={{ title: "Messages" }} />
        <Stack.Screen name="support" options={{ title: "Support" }} />
        <Stack.Screen name="account" options={{ title: "My Account" }} />
      </Stack>
    </AuthProvider>
  );
}

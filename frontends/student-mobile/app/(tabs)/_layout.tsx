import { Redirect, Tabs } from "expo-router";
import { Text } from "react-native";
import { useAuth } from "../../src/auth";
import { Loading } from "../../src/components";
import { C } from "../../src/theme";

const I = ({ children }: { children: string }) => (
  <Text style={{ fontSize: 15, fontWeight: "900" }}>
    {children}
  </Text>
);

export default function TabsLayout() {
  const auth = useAuth();

  if (auth.hydrating) {
    return <Loading text="Loading Student App..." />;
  }

  if (!auth.fullAccess) {
    return <Redirect href="/login" />;
  }

  return (
    <Tabs
      screenOptions={{
        headerStyle: { backgroundColor: C.navy },
        headerTintColor: "#FFFFFF",
        headerTitleStyle: { fontWeight: "800" },
        tabBarActiveTintColor: C.navy,
        tabBarInactiveTintColor: C.muted,
        tabBarStyle: {
          height: 66,
          paddingBottom: 7,
          paddingTop: 6,
        },
        tabBarLabelStyle: {
          fontSize: 10,
          fontWeight: "800",
        },
      }}
    >
      <Tabs.Screen
        name="dashboard"
        options={{
          title: "Dashboard",
          tabBarIcon: () => <I>⌂</I>,
        }}
      />
      <Tabs.Screen
        name="learning"
        options={{
          title: "Learning",
          tabBarIcon: () => <I>▦</I>,
        }}
      />
      <Tabs.Screen
        name="documents"
        options={{
          title: "Documents",
          tabBarIcon: () => <I>▤</I>,
        }}
      />
      <Tabs.Screen
        name="finance"
        options={{
          title: "Finance",
          tabBarIcon: () => <I>R</I>,
        }}
      />
      <Tabs.Screen
        name="more"
        options={{
          title: "More",
          tabBarIcon: () => <I>•••</I>,
        }}
      />
    </Tabs>
  );
}

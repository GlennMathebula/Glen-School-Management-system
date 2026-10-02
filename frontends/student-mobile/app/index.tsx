import { Redirect } from "expo-router";
import { Loading } from "../src/components";
import { useAuth } from "../src/auth";

export default function Index() {
  const auth = useAuth();

  if (auth.hydrating) {
    return <Loading text="Opening Student App..." />;
  }

  if (auth.fullAccess) {
    return <Redirect href="/(tabs)/dashboard" />;
  }

  if (auth.needsOnboarding) {
    return <Redirect href="/onboarding" />;
  }

  return <Redirect href="/login" />;
}

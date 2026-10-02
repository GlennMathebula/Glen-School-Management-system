import * as Sharing from "expo-sharing";
import * as FileSystem from "expo-file-system/legacy";
import { API_BASE } from "./api";

export async function downloadProtected(
  path: string,
  token: string,
  filename: string
) {
  if (!FileSystem.cacheDirectory) {
    throw new Error("Device cache directory is unavailable.");
  }

  const safe = filename.replace(/[^a-zA-Z0-9._-]+/g, "_");
  const target = `${FileSystem.cacheDirectory}${Date.now()}_${safe}`;

  const result = await FileSystem.downloadAsync(
    `${API_BASE}${path}`,
    target,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (await Sharing.isAvailableAsync()) {
    await Sharing.shareAsync(result.uri, {
      dialogTitle: filename,
    });
  }

  return result.uri;
}

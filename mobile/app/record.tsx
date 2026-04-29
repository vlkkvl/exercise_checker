/**
 * Screen 2 — Record / Upload
 * User records a new video or picks one from the gallery, then uploads it.
 */
import { useState } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  Image,
} from "react-native";
import * as ImagePicker from "expo-image-picker";
import { useLocalSearchParams, useRouter } from "expo-router";
import { analyzeVideo, ApiError, type ExerciseType } from "../src/api";

const EXERCISE_LABELS: Record<ExerciseType, string> = {
  pushups: "Push-ups",
  squats: "Squats",
  bicep_curls: "Bicep Curls",
};

export default function RecordScreen() {
  const { exercise } = useLocalSearchParams<{ exercise: ExerciseType }>();
  const router = useRouter();

  const [videoUri, setVideoUri] = useState<string | null>(null);
  const [thumbnail, setThumbnail] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function pickFromGallery() {
    const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!perm.granted) {
      Alert.alert("Permission required", "Allow access to your photo library.");
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Videos,
      allowsEditing: false,
      quality: 1,
      videoMaxDuration: 60,
    });
    if (!result.canceled && result.assets[0]) {
      setVideoUri(result.assets[0].uri);
      setThumbnail(null);
    }
  }

  async function recordVideo() {
    const perm = await ImagePicker.requestCameraPermissionsAsync();
    if (!perm.granted) {
      Alert.alert("Permission required", "Allow camera access to record.");
      return;
    }
    const result = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Videos,
      videoMaxDuration: 60,
      quality: 1,
    });
    if (!result.canceled && result.assets[0]) {
      setVideoUri(result.assets[0].uri);
      setThumbnail(null);
    }
  }

  async function submit() {
    if (!videoUri || !exercise) return;
    setLoading(true);
    try {
      const result = await analyzeVideo(videoUri, exercise);
      router.push({
        pathname: "/results",
        params: {
          passed: String(result.passed),
          feedback: JSON.stringify(result.feedback),
          exercise,
        },
      });
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? err.message
          : "Something went wrong. Please try again.";
      Alert.alert("Analysis failed", msg);
    } finally {
      setLoading(false);
    }
  }

  const label = exercise ? EXERCISE_LABELS[exercise] : "Exercise";

  return (
    <View style={styles.container}>
      <Text style={styles.heading}>{label}</Text>
      <Text style={styles.subheading}>
        Record a 5–15 second clip from the side or front so your full body is
        visible. Keep it under 60 seconds.
      </Text>

      <View style={styles.buttonRow}>
        <TouchableOpacity
          style={[styles.actionBtn, styles.btnOutline]}
          onPress={recordVideo}
          disabled={loading}
        >
          <Text style={styles.btnOutlineText}>Record</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.actionBtn, styles.btnOutline]}
          onPress={pickFromGallery}
          disabled={loading}
        >
          <Text style={styles.btnOutlineText}>Pick Video</Text>
        </TouchableOpacity>
      </View>

      {videoUri && (
        <View style={styles.previewBox}>
          {thumbnail ? (
            <Image source={{ uri: thumbnail }} style={styles.thumbnail} />
          ) : (
            <Text style={styles.videoReady}>Video selected</Text>
          )}
          <Text style={styles.videoUri} numberOfLines={1}>
            {videoUri.split("/").pop()}
          </Text>
        </View>
      )}

      <TouchableOpacity
        style={[styles.submitBtn, (!videoUri || loading) && styles.submitDisabled]}
        onPress={submit}
        disabled={!videoUri || loading}
        activeOpacity={0.85}
      >
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.submitText}>Analyse Form</Text>
        )}
      </TouchableOpacity>

      {loading && (
        <Text style={styles.loadingHint}>
          Uploading and analysing… this may take 10–30 seconds.
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 24 },
  heading: {
    fontSize: 26,
    fontWeight: "800",
    color: "#1a1a2e",
    marginBottom: 8,
    marginTop: 8,
  },
  subheading: {
    fontSize: 14,
    color: "#666",
    lineHeight: 21,
    marginBottom: 28,
  },
  buttonRow: {
    flexDirection: "row",
    gap: 12,
    marginBottom: 24,
  },
  actionBtn: {
    flex: 1,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
  },
  btnOutline: {
    borderWidth: 2,
    borderColor: "#6c47ff",
    backgroundColor: "#fff",
  },
  btnOutlineText: {
    color: "#6c47ff",
    fontSize: 16,
    fontWeight: "700",
  },
  previewBox: {
    backgroundColor: "#fff",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#e0e0e0",
    padding: 16,
    alignItems: "center",
    marginBottom: 28,
  },
  thumbnail: {
    width: "100%",
    height: 180,
    borderRadius: 8,
    marginBottom: 8,
  },
  videoReady: {
    fontSize: 16,
    color: "#333",
    marginBottom: 4,
  },
  videoUri: {
    fontSize: 12,
    color: "#999",
    textAlign: "center",
  },
  submitBtn: {
    backgroundColor: "#6c47ff",
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: "center",
  },
  submitDisabled: {
    backgroundColor: "#b0a0e0",
  },
  submitText: {
    color: "#fff",
    fontSize: 18,
    fontWeight: "700",
  },
  loadingHint: {
    marginTop: 14,
    textAlign: "center",
    color: "#888",
    fontSize: 13,
  },
});

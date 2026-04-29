/**
 * Screen 3 — Results
 * Displays pass/fail verdict and bullet-point feedback.
 */
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import type { ExerciseType } from "../src/api";

const EXERCISE_LABELS: Record<ExerciseType, string> = {
  pushups: "Push-ups",
  squats: "Squats",
  bicep_curls: "Bicep Curls",
};

export default function ResultsScreen() {
  const { passed, feedback, exercise } = useLocalSearchParams<{
    passed: string;
    feedback: string;
    exercise: ExerciseType;
  }>();
  const router = useRouter();

  const isGood = passed === "true";
  const feedbackList: string[] = feedback ? JSON.parse(feedback) : [];
  const label = exercise ? EXERCISE_LABELS[exercise] : "Exercise";

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={[styles.verdictCard, isGood ? styles.passCard : styles.failCard]}>
        <Text style={styles.verdictEmoji}>{isGood ? "✅" : "❌"}</Text>
        <Text style={styles.verdictTitle}>
          {isGood ? "Good Form!" : "Needs Work"}
        </Text>
        <Text style={styles.verdictSub}>{label}</Text>
      </View>

      <Text style={styles.feedbackHeading}>Feedback</Text>

      {feedbackList.map((item, i) => (
        <View key={i} style={styles.feedbackItem}>
          <Text style={styles.bullet}>{isGood ? "•" : "⚠️"}</Text>
          <Text style={styles.feedbackText}>{item}</Text>
        </View>
      ))}

      <TouchableOpacity
        style={styles.retryBtn}
        onPress={() => router.push({ pathname: "/record", params: { exercise } })}
        activeOpacity={0.85}
      >
        <Text style={styles.retryText}>Try Again</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.homeBtn}
        onPress={() => router.push("/")}
        activeOpacity={0.85}
      >
        <Text style={styles.homeText}>Change Exercise</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 24,
    paddingBottom: 48,
  },
  verdictCard: {
    borderRadius: 16,
    padding: 28,
    alignItems: "center",
    marginBottom: 32,
  },
  passCard: {
    backgroundColor: "#e8f5e9",
    borderWidth: 1.5,
    borderColor: "#66bb6a",
  },
  failCard: {
    backgroundColor: "#fff3e0",
    borderWidth: 1.5,
    borderColor: "#ffa726",
  },
  verdictEmoji: {
    fontSize: 48,
    marginBottom: 8,
  },
  verdictTitle: {
    fontSize: 26,
    fontWeight: "800",
    color: "#1a1a2e",
    marginBottom: 4,
  },
  verdictSub: {
    fontSize: 15,
    color: "#666",
  },
  feedbackHeading: {
    fontSize: 18,
    fontWeight: "700",
    color: "#1a1a2e",
    marginBottom: 14,
  },
  feedbackItem: {
    flexDirection: "row",
    alignItems: "flex-start",
    backgroundColor: "#fff",
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: "#ececec",
    gap: 10,
  },
  bullet: {
    fontSize: 16,
    lineHeight: 22,
  },
  feedbackText: {
    flex: 1,
    fontSize: 15,
    color: "#333",
    lineHeight: 22,
  },
  retryBtn: {
    marginTop: 28,
    backgroundColor: "#6c47ff",
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: "center",
    marginBottom: 12,
  },
  retryText: {
    color: "#fff",
    fontSize: 17,
    fontWeight: "700",
  },
  homeBtn: {
    borderWidth: 2,
    borderColor: "#6c47ff",
    borderRadius: 14,
    paddingVertical: 14,
    alignItems: "center",
  },
  homeText: {
    color: "#6c47ff",
    fontSize: 17,
    fontWeight: "700",
  },
});

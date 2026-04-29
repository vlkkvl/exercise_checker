/**
 * Screen 1 — Home
 * User picks an exercise type and taps "Start".
 */
import { useState } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Platform,
} from "react-native";
import { Picker } from "@react-native-picker/picker";
import { useRouter } from "expo-router";
import type { ExerciseType } from "../src/api";

const EXERCISES: { label: string; value: ExerciseType }[] = [
  { label: "Push-ups", value: "pushups" },
  { label: "Squats", value: "squats" },
  { label: "Bicep Curls", value: "bicep_curls" },
];

export default function HomeScreen() {
  const [exercise, setExercise] = useState<ExerciseType>("pushups");
  const router = useRouter();

  return (
    <View style={styles.container}>
      <Text style={styles.heading}>Select Exercise</Text>
      <Text style={styles.subheading}>
        Record or upload a short clip of yourself performing the exercise.
        We'll analyse your form and give you feedback.
      </Text>

      <View style={styles.pickerWrapper}>
        <Picker
          selectedValue={exercise}
          onValueChange={(v) => setExercise(v as ExerciseType)}
          style={styles.picker}
          itemStyle={styles.pickerItem}
        >
          {EXERCISES.map((ex) => (
            <Picker.Item key={ex.value} label={ex.label} value={ex.value} />
          ))}
        </Picker>
      </View>

      <TouchableOpacity
        style={styles.button}
        onPress={() => router.push({ pathname: "/record", params: { exercise } })}
        activeOpacity={0.85}
      >
        <Text style={styles.buttonText}>Continue →</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 24,
    justifyContent: "center",
  },
  heading: {
    fontSize: 28,
    fontWeight: "800",
    color: "#1a1a2e",
    marginBottom: 10,
  },
  subheading: {
    fontSize: 15,
    color: "#555",
    lineHeight: 22,
    marginBottom: 32,
  },
  pickerWrapper: {
    backgroundColor: "#fff",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#e0e0e0",
    marginBottom: 32,
    overflow: "hidden",
  },
  picker: {
    width: "100%",
    height: Platform.OS === "ios" ? 180 : 52,
  },
  pickerItem: {
    fontSize: 18,
  },
  button: {
    backgroundColor: "#6c47ff",
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: "center",
  },
  buttonText: {
    color: "#fff",
    fontSize: 18,
    fontWeight: "700",
  },
});

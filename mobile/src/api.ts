import { API_BASE_URL } from "./config";

export type ExerciseType = "pushups" | "squats" | "bicep_curls";

export interface AnalysisResult {
  exercise: ExerciseType;
  passed: boolean;
  feedback: string[];
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
  }
}

export async function analyzeVideo(
  videoUri: string,
  exercise: ExerciseType
): Promise<AnalysisResult> {
  const form = new FormData();
  form.append("exercise", exercise);
  form.append("video", {
    uri: videoUri,
    name: "exercise.mp4",
    type: "video/mp4",
  } as unknown as Blob);

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 60_000);

  try {
    const res = await fetch(`${API_BASE_URL}/analyze`, {
      method: "POST",
      body: form,
      signal: controller.signal,
    });

    if (!res.ok) {
      let detail = `Server error (${res.status})`;
      try {
        const json = await res.json();
        detail = json.detail ?? detail;
      } catch {}
      throw new ApiError(res.status, detail);
    }

    return res.json() as Promise<AnalysisResult>;
  } catch (err) {
    if (err instanceof ApiError) throw err;
    if ((err as Error).name === "AbortError") {
      throw new ApiError(0, "Request timed out. Check your network connection.");
    }
    throw new ApiError(0, "Could not reach the server. Is the backend running?");
  } finally {
    clearTimeout(timeout);
  }
}

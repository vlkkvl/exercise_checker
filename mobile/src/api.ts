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

const REQUEST_TIMEOUT_MS = 60_000;

export async function analyzeVideo(
  videoUri: string,
  exercise: ExerciseType
): Promise<AnalysisResult> {
  const url = `${API_BASE_URL}/analyze`;
  console.log("[analyzeVideo] start", { url, exercise, videoUri });
  console.log("API_BASE_URL =", API_BASE_URL);

  const form = new FormData();
  form.append("exercise", exercise);
  form.append("video", {
    uri: videoUri,
    name: "exercise.mp4",
    type: "video/mp4",
  } as unknown as Blob);

  const controller = new AbortController();
  const timeout = setTimeout(() => {
    console.warn(`[analyzeVideo] aborting after ${REQUEST_TIMEOUT_MS}ms timeout`);
    controller.abort();
  }, REQUEST_TIMEOUT_MS);

  const startedAt = Date.now();
  try {
    console.log("[analyzeVideo] sending request…");
    const res = await fetch(url, {
      method: "POST",
      body: form,
      signal: controller.signal,
    });
    console.log(
      `[analyzeVideo] response received status=${res.status} after ${Date.now() - startedAt}ms`
    );

    if (!res.ok) {
      let detail = `Server error (${res.status})`;
      try {
        const json = await res.json();
        detail = json.detail ?? detail;
      } catch (parseErr) {
        console.warn("[analyzeVideo] failed to parse error body", parseErr);
      }
      console.warn("[analyzeVideo] non-OK response", { status: res.status, detail });
      throw new ApiError(res.status, detail);
    }

    const json = (await res.json()) as AnalysisResult;
    console.log(
      `[analyzeVideo] success after ${Date.now() - startedAt}ms passed=${json.passed} feedbackCount=${json.feedback?.length ?? 0}`
    );
    return json;
  } catch (err) {
    const elapsed = Date.now() - startedAt;
    if (err instanceof ApiError) {
      console.warn(`[analyzeVideo] api error after ${elapsed}ms`, err.status, err.message);
      throw err;
    }
    const name = (err as Error)?.name;
    if (name === "AbortError") {
      console.warn(`[analyzeVideo] aborted after ${elapsed}ms (client timeout)`);
      throw new ApiError(0, "Request timed out. Check your network connection.");
    }
    console.warn(`[analyzeVideo] network/unknown error after ${elapsed}ms`, err);
    throw new ApiError(0, "Could not reach the server. Is the backend running?");
  } finally {
    clearTimeout(timeout);
  }
}

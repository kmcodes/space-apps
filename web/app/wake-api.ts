// Render's free plan puts the engine API to sleep when it is idle, and the first request after that can take
// about a minute. A plain GET /health sent as soon as the page opens (and again when the call starts) wakes it
// while the farmer is still answering questions, so the results are ready when the form ends.
// It sends nothing about the farmer: no body, no cookies, no answers.

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
const MIN_GAP_MS = 20_000; // do not ping more than once every 20 s
let lastPing = 0;

export function wakeApi() {
  if (typeof window === "undefined") return;
  const now = Date.now();
  if (now - lastPing < MIN_GAP_MS) return;
  lastPing = now;
  fetch(`${API_URL}/health`, { cache: "no-store" }).catch(() => {
    // Offline or still waking: the results screen retries on its own, so nothing to do here.
  });
}

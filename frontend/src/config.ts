const apiBaseFromEnv = import.meta.env.VITE_API_BASE_URL;

export const API_BASE = apiBaseFromEnv || window.location.origin;

export function websocketUrl(path: string) {
  const base = new URL(API_BASE);
  base.protocol = base.protocol === "https:" ? "wss:" : "ws:";
  base.pathname = path;
  base.search = "";
  return base.toString();
}


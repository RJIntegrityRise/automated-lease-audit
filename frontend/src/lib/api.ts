import { createClient } from "@/lib/supabase";

const apiUrl =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

export async function authenticatedFetch(
  path: string,
  init: RequestInit = {},
) {
  const supabase = createClient();

  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session?.access_token) {
    throw new Error("Authentication required.");
  }

  const headers = new Headers(init.headers);

  headers.set(
    "Authorization",
    `Bearer ${session.access_token}`,
  );

  return fetch(`${apiUrl}${path}`, {
    ...init,
    headers,
  });
}
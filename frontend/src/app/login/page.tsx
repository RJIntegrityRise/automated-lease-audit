"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { createClient } from "@/lib/supabase";

export default function LoginPage() {
  const router = useRouter();
  const supabase = createClient();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setLoading(true);
    setError(null);

    const {
        data: signInData,
      error: signInError,
    } = await supabase.auth.signInWithPassword({
        email,
        password,
    });

    if (signInError || !signInData.user) {
        setError(
        signInError?.message ??
            "Unable to sign in.",
        );
        setLoading(false);
        return;
    }

    const { data: profile, error: profileError } =
        await supabase
        .from("profiles")
        .select("role, active, approval_status")
        .eq("id", signInData.user.id)
        .single();

    if (profileError || !profile) {
        await supabase.auth.signOut();

        setError(
        "Unable to verify your account access.",
        );

        setLoading(false);
        return;
    }

    if (!profile.active) {
        await supabase.auth.signOut();

        setError(
        "Your account has been disabled. Contact an administrator.",
        );

        setLoading(false);
        return;
    }

    if (profile.approval_status === "pending") {
        router.push("/pending");
        router.refresh();
        return;
    }

    if (profile.approval_status !== "approved") {
        await supabase.auth.signOut();

        setError(
        "Your account is not approved to use this application.",
        );

        setLoading(false);
        return;
    }

    router.push("/");
    router.refresh();
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4 text-foreground">
      <div className="w-full max-w-md rounded-xl border bg-card p-8 shadow-sm">
        <div className="mb-8">
          <p className="text-sm font-semibold uppercase tracking-wider text-blue-600 dark:text-blue-400">
            Lease Audit
          </p>

          <h1 className="mt-2 text-3xl font-bold">
            Sign in
          </h1>

          <p className="mt-2 text-sm text-muted-foreground">
            Sign in with your approved company account.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-5"
        >
          <div>
            <label
              htmlFor="email"
              className="mb-2 block text-sm font-medium"
            >
              Email
            </label>

            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              className="w-full rounded-md border bg-background px-3 py-2 outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="you@company.com"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="mb-2 block text-sm font-medium"
            >
              Password
            </label>

            <input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              className="w-full rounded-md border bg-background px-3 py-2 outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter your password"
            />
          </div>

          {error ? (
            <div className="rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
              {error}
            </div>
          ) : null}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-blue-600 px-4 py-2.5 font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <div className="mt-5 space-y-3 text-center">
            <a
                href="/forgot-password"
                className="block text-sm font-medium text-blue-600 hover:underline dark:text-blue-400"
            >
                Forgot password?
            </a>

            <a
                href="/signup"
                className="block text-sm font-medium text-blue-600 hover:underline dark:text-blue-400"
            >
                Create account
            </a>
        </div>






      </div>
    </main>
  );
}
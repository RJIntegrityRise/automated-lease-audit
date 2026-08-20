"use client";

import {
  FormEvent,
  useEffect,
  useState,
} from "react";

import { useRouter } from "next/navigation";

import { createClient } from "@/lib/supabase";

const PASSWORD_REGEX =
  /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/;



export default function ResetPasswordPage() {
  const router = useRouter();
  const supabase = createClient();

  const [password, setPassword] =
    useState("");

  const [
    confirmPassword,
    setConfirmPassword,
  ] = useState("");

  const [loading, setLoading] =
    useState(false);

  const [
    checkingRecovery,
    setCheckingRecovery,
  ] = useState(true);

  const [
    recoveryVerified,
    setRecoveryVerified,
  ] = useState(false);

  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    let recoveryDetected = false;

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(
      (event) => {
        if (event === "PASSWORD_RECOVERY") {
          recoveryDetected = true;
          setRecoveryVerified(true);
          setCheckingRecovery(false);
        }
      },
    );

    const timeout = window.setTimeout(
      () => {
        if (!recoveryDetected) {
          setCheckingRecovery(false);
        }
      },
      1500,
    );

    return () => {
      window.clearTimeout(timeout);
      subscription.unsubscribe();
    };
  }, [supabase]);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (!recoveryVerified) {
      setError(
        "Password recovery has not been verified.",
      );
      return;
    }

    setError(null);

    if (!PASSWORD_REGEX.test(password)) {
        setError(
            "Password must be at least 8 characters and include uppercase, lowercase, number, and special character.",
        );
        return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);

    const { error: updateError } =
      await supabase.auth.updateUser({
        password,
      });

    if (updateError) {
      setError(updateError.message);
      setLoading(false);
      return;
    }

    await supabase.auth.signOut();

    router.push(
      "/login?password_reset=success",
    );

    router.refresh();
  }

  if (checkingRecovery) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background px-4 text-foreground">
        <p className="text-sm text-muted-foreground">
          Verifying password recovery link...
        </p>
      </main>
    );
  }

  if (!recoveryVerified) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background px-4 text-foreground">
        <div className="w-full max-w-md rounded-xl border bg-card p-8 text-center shadow-sm">
          <h1 className="text-2xl font-bold">
            Invalid recovery link
          </h1>

          <p className="mt-3 text-sm text-muted-foreground">
            You must request a password reset
            and open the secure link sent to
            your email before choosing a new
            password.
          </p>

          <a
            href="/forgot-password"
            className="mt-6 inline-block rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Request password reset
          </a>
        </div>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4 text-foreground">
      <div className="w-full max-w-md rounded-xl border bg-card p-8 shadow-sm">
        <h1 className="text-2xl font-bold">
          Choose a new password
        </h1>

        <p className="mt-2 text-sm text-muted-foreground">
          Your password recovery link has
          been verified.
        </p>

        <form
          onSubmit={handleSubmit}
          className="mt-6 space-y-5"
        >
          <div>
            <label
              htmlFor="password"
              className="mb-2 block text-sm font-medium"
            >
              New password
            </label>

            <input
              id="password"
              type="password"
              autoComplete="new-password"
              required
              value={password}
              onChange={(event) =>
                setPassword(
                  event.target.value,
                )
              }
              className="w-full rounded-md border bg-background px-3 py-2"
            />
          </div>

          <div>
            <label
              htmlFor="confirmPassword"
              className="mb-2 block text-sm font-medium"
            >
              Confirm password
            </label>

            <input
              id="confirmPassword"
              type="password"
              autoComplete="new-password"
              required
              value={confirmPassword}
              onChange={(event) =>
                setConfirmPassword(
                  event.target.value,
                )
              }
              className="w-full rounded-md border bg-background px-3 py-2"
            />
          </div>

          {error ? (
            <p className="text-sm text-red-600">
              {error}
            </p>
          ) : null}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-blue-600 px-4 py-2.5 font-medium text-white disabled:opacity-60"
          >
            {loading
              ? "Updating..."
              : "Update password"}
          </button>
        </form>
      </div>
    </main>
  );
}
"use client";

import { useRouter } from "next/navigation";

import { createClient } from "@/lib/supabase";

export default function PendingPage() {
  const router = useRouter();
  const supabase = createClient();

  async function handleSignOut() {
    await supabase.auth.signOut();
    router.push("/login");
    router.refresh();
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4 text-foreground">
      <div className="w-full max-w-md rounded-xl border bg-card p-8 text-center shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wider text-blue-600 dark:text-blue-400">
          Lease Audit
        </p>

        <h1 className="mt-3 text-2xl font-bold">
          Approval pending
        </h1>

        <p className="mt-3 text-sm text-muted-foreground">
          Your account has been created, but an administrator must approve it before you can use the lease audit system.
        </p>

        <button
          type="button"
          onClick={handleSignOut}
          className="mt-6 rounded-md border px-4 py-2 text-sm font-medium hover:bg-muted"
        >
          Sign out
        </button>
      </div>
    </main>
  );
}
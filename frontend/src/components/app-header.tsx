"use client";

import {
  FileSearch,
  LogOut,
  Shield,
} from "lucide-react";
import Link from "next/link";
import {
  useEffect,
  useMemo,
  useState,
} from "react";
import { useRouter } from "next/navigation";

import { ThemeToggle } from "@/components/theme-toggle";
import { createClient } from "@/lib/supabase";

type UserRole =
  | "master_admin"
  | "admin"
  | "manager"
  | "reviewer";

export function AppHeader() {
  const router = useRouter();

  const supabase = useMemo(
    () => createClient(),
    [],
  );

  const [role, setRole] =
    useState<UserRole | null>(null);

  useEffect(() => {
    async function loadRole() {
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session) {
        return;
      }

      const { data: profile } =
        await supabase
          .from("profiles")
          .select("role")
          .eq("id", session.user.id)
          .single();

      if (profile) {
        setRole(
          profile.role as UserRole,
        );
      }
    }

    void loadRole();
  }, [supabase]);

  async function handleLogout() {
    await supabase.auth.signOut();

    router.push("/login");
    router.refresh();
  }

  const canManageUsers =
    role === "admin" ||
    role === "master_admin";

  return (
    <header className="border-b border-border bg-card text-card-foreground">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-3">
          <FileSearch className="h-6 w-6" />

          <div>
            <h1 className="font-semibold">
              Automated Lease Audit
            </h1>

            <p className="text-sm text-muted-foreground">
              Upload and review residential leases
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Link
            href="/dashboard"
            className="rounded-md px-3 py-2 text-sm font-medium hover:bg-muted"
          >
            Dashboard
          </Link>

          <Link
            href="/"
            className="rounded-md px-3 py-2 text-sm font-medium hover:bg-muted"
          >
            Upload Lease
          </Link>

          {canManageUsers ? (
            <Link
              href="/admin/users"
              className="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium hover:bg-muted"
            >
              <Shield className="h-4 w-4" />
              User Management
            </Link>
          ) : null}

          <ThemeToggle />

          <button
            type="button"
            onClick={handleLogout}
            className="flex items-center gap-2 rounded-md border px-3 py-2 text-sm font-medium hover:bg-muted"
          >
            <LogOut className="h-4 w-4" />
            Logout
          </button>
        </div>
      </div>
    </header>
  );
}
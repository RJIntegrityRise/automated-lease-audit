"use client";

import {
  ReactNode,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useRouter } from "next/navigation";

import { createClient } from "@/lib/supabase";

export type AppRole =
  | "master_admin"
  | "admin"
  | "manager"
  | "reviewer";

type AuthGuardProps = {
  children: ReactNode;
  allowedRoles?: AppRole[];
};

export function AuthGuard({
  children,
  allowedRoles,
}: AuthGuardProps) {
  const router = useRouter();

  const supabase = useMemo(
    () => createClient(),
    [],
  );

  const [allowed, setAllowed] =
    useState(false);

  useEffect(() => {
    async function checkAccess() {
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session) {
        router.replace("/login");
        return;
      }

      const { data: profile } =
        await supabase
          .from("profiles")
          .select(
            "role, active, approval_status",
          )
          .eq(
            "id",
            session.user.id,
          )
          .single();

      if (!profile) {
        await supabase.auth.signOut();
        router.replace("/login");
        return;
      }

      if (!profile.active) {
        await supabase.auth.signOut();
        router.replace("/login");
        return;
      }

      if (
        profile.approval_status ===
        "pending"
      ) {
        router.replace("/pending");
        return;
      }

      if (
        profile.approval_status !==
        "approved"
      ) {
        await supabase.auth.signOut();
        router.replace("/login");
        return;
      }

      if (
        allowedRoles &&
        !allowedRoles.includes(
          profile.role as AppRole,
        )
      ) {
        router.replace("/dashboard");
        return;
      }

      setAllowed(true);
    }

    void checkAccess();
  }, [
    allowedRoles,
    router,
    supabase,
  ]);

  if (!allowed) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background text-foreground">
        <p className="text-sm text-muted-foreground">
          Checking access...
        </p>
      </div>
    );
  }

  return <>{children}</>;
}
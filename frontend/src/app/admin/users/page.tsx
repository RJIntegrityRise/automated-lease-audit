"use client";


import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import { createClient } from "@/lib/supabase";
import { AuthGuard } from "@/components/auth-guard";
import { useRouter } from "next/navigation";






type UserRole =
  | "master_admin"
  | "admin"
  | "manager"
  | "reviewer";

type ApprovalStatus =
  | "pending"
  | "approved"
  | "rejected";

type AdminUser = {
  id: string;
  email: string | null;
  full_name: string | null;
  role: UserRole;
  active: boolean;
  approval_status: ApprovalStatus;
  approved_by: string | null;
  approved_at: string | null;
  created_at: string;
};

type ActionName =
  | "approve"
  | "reject"
  | "enable"
  | "disable"
  | "set_role";

const apiUrl =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

export default function AdminUsersPage() {
  return (
    <AuthGuard
      allowedRoles={[
        "admin",
        "master_admin",
      ]}
    >
      <AdminUsersContent />
    </AuthGuard>
  );
}

function AdminUsersContent() {
  const supabase = useMemo(
    () => createClient(),
    [],
  );

  const router = useRouter();

  const [users, setUsers] =
    useState<AdminUser[]>([]);

  const [currentRole, setCurrentRole] =
    useState<UserRole | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [actionUserId, setActionUserId] =
    useState<string | null>(null);

  const [error, setError] =
    useState<string | null>(null);

  const getAccessToken = useCallback(async () => {
    const {
        data: { session },
    } = await supabase.auth.getSession();

    return session?.access_token ?? null;
  }, [supabase]);

  const loadUsers = useCallback(async () => { 
    setLoading(true);
    setError(null);

    const token = await getAccessToken();

    if (!token) {
      router.push("/login");
      return;
    }

    const {
        data: { session },
    } = await supabase.auth.getSession();

    if (!session) {
        router.push("/login");
        return;
    }

    const { data: profile } =
        await supabase
            .from("profiles")
            .select("role")
            .eq("id", session.user.id)
            .single();

    if (!profile) {
      setError(
        "Unable to load your profile.",
      );
      setLoading(false);
      return;
    }

    setCurrentRole(
      profile.role as UserRole,
    );

    const response = await fetch(
      `${apiUrl}/api/admin/users`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    );

    if (!response.ok) {
      const body = await response
        .json()
        .catch(() => null);

      setError(
        body?.detail ??
          "Unable to load users.",
      );

      setLoading(false);
      return;
    }

    const data =
      (await response.json()) as AdminUser[];

    setUsers(data);
    setLoading(false);
  }, [getAccessToken, router, supabase]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
        void loadUsers();
    }, 0);

    return () => {
        window.clearTimeout(timer);
    };
  }, [loadUsers]);

  async function updateUser(
    userId: string,
    action: ActionName,
    role?: UserRole,
  ) {
    setActionUserId(userId);
    setError(null);

    const token = await getAccessToken();

    if (!token) {
      router.push("/login");
      return;
    }

    const response = await fetch(
      `${apiUrl}/api/admin/users/${userId}`,
      {
        method: "PATCH",
        headers: {
          "Content-Type":
            "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          action,
          role,
        }),
      },
    );

    if (!response.ok) {
      const body = await response
        .json()
        .catch(() => null);

      setError(
        body?.detail ??
          "Unable to update user.",
      );

      setActionUserId(null);
      return;
    }

    await loadUsers();
    setActionUserId(null);
  }

  if (loading) {
    return (
      <main className="min-h-screen bg-background px-6 py-10 text-foreground">
        <p className="text-sm text-muted-foreground">
          Loading users...
        </p>
      </main>
    );
  }

  return (
    
      <main className="min-h-screen bg-background px-6 py-10 text-foreground">
        <div className="mx-auto max-w-7xl">
          <div className="mb-8">
            <p className="text-sm font-semibold uppercase tracking-wider text-blue-600 dark:text-blue-400">
              Administration
            </p>
  
            <h1 className="mt-2 text-3xl font-bold">
              User management
            </h1>

            <p className="mt-2 text-sm text-muted-foreground">
              Approve accounts, manage access,
              and assign administrative roles.
            </p>
          </div>

          {error ? (
            <div className="mb-6 rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
              {error}
            </div>
          ) : null}
 
          <div className="overflow-x-auto rounded-xl border">
            <table className="w-full text-left text-sm">
              <thead className="bg-muted/50">
                <tr>
                  <th className="px-4 py-3">
                    User
                  </th>

                  <th className="px-4 py-3">
                    Role
                  </th>

                  <th className="px-4 py-3">
                    Approval
                  </th>

                  <th className="px-4 py-3">
                    Active
                  </th>

                  <th className="px-4 py-3">
                    Actions
                  </th>
                </tr>
              </thead>
  
              <tbody>
                {users.map((user) => {
                  const busy =
                    actionUserId === user.id;

                  const canManageNormalUser =
                    currentRole === "master_admin" ||
                    (currentRole === "admin" &&
                    user.role !== "admin" &&
                    user.role !== "master_admin");  
  
                  return (
                    <tr
                      key={user.id}
                      className="border-t"
                    >
                      <td className="px-4 py-4">
                        <div className="font-medium">
                          {user.full_name ||
                            "Unnamed user"}
                        </div>
  
                        <div className="text-xs text-muted-foreground">
                          {user.email ??
                            "No email"}
                        </div>
                      </td>
 
                      <td className="px-4 py-4">
                        {user.role}
                      </td>
  
                      <td className="px-4 py-4">
                        {user.approval_status}
                      </td>
  
                      <td className="px-4 py-4">
                        {user.active
                          ? "Yes"
                          : "No"}
                      </td>
  
                      <td className="px-4 py-4">
                        <div className="flex flex-wrap gap-2">
                          {canManageNormalUser ? (
                            <>
                                {user.approval_status !==
                                "approved" ? (
                                    <button
                                        type="button"
                                        disabled={busy}
                                        onClick={() =>
                                            updateUser(
                                                user.id,
                                                "approve",
                                            )
                                        }
                                        className="rounded-md bg-green-600 px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50"
                                    >
                                        Approve
                                    </button>
                                ) : null}

                                {user.approval_status ===
                                "pending" ? (
                                    <button
                                        type="button"
                                        disabled={busy}
                                        onClick={() =>
                                            updateUser(
                                                user.id,
                                                "reject",
                                            )
                                        }
                                        className="rounded-md border px-3 py-1.5 text-xs font-medium disabled:opacity-50"
                                    >
                                        Reject
                                    </button>
                                ) : null}

                                {user.active ? (
                                    <button
                                        type="button"
                                        disabled={busy}
                                        onClick={() =>
                                            updateUser(
                                                user.id,
                                                "disable",
                                            )
                                        }
                                        className="rounded-md border px-3 py-1.5 text-xs font-medium disabled:opacity-50"
                                    >
                                        Disable
                                    </button>
                                ) : (
                                    <button
                                        type="button"
                                        disabled={busy}
                                        onClick={() =>
                                            updateUser(
                                                user.id,
                                                "enable",
                                            )
                                        }
                                        className="rounded-md border px-3 py-1.5 text-xs font-medium disabled:opacity-50"
                                    >
                                        Enable
                                    </button>
                                )}
                            </>
                        ) : null}

                          {currentRole ===
                          "master_admin" ? (
                            <>
                              {user.role ===
                              "reviewer" ? (
                                <button
                                  type="button"
                                  disabled={busy}
                                  onClick={() =>
                                    updateUser(
                                      user.id,
                                      "set_role",
                                      "admin",
                                    )
                                  }
                                  className="rounded-md border px-3 py-1.5 text-xs font-medium disabled:opacity-50"
                                >
                                  Make admin
                                </button>
                              ) : null}
  
                              {user.role ===
                              "admin" ? (
                                <>
                                  <button
                                    type="button"
                                    disabled={busy}
                                    onClick={() =>
                                      updateUser(
                                        user.id,
                                        "set_role",
                                        "master_admin",
                                      )
                                    }
                                    className="rounded-md border px-3 py-1.5 text-xs font-medium disabled:opacity-50"
                                  >
                                    Make master admin
                                  </button>

                                  <button
                                    type="button"
                                    disabled={busy}
                                    onClick={() =>
                                      updateUser(
                                        user.id,
                                        "set_role",
                                        "reviewer",
                                      )
                                    }
                                    className="rounded-md border px-3 py-1.5 text-xs font-medium disabled:opacity-50"
                                  >
                                    Remove admin
                                  </button>
                                </>
                              ) : null}

                              {user.role ===
                              "master_admin" ? (
                                <button
                                  type="button"
                                  disabled={busy}
                                  onClick={() =>
                                    updateUser(
                                      user.id,
                                      "set_role",
                                      "admin",
                                    )
                                  }
                                  className="rounded-md border px-3 py-1.5 text-xs font-medium disabled:opacity-50"
                                >
                                  Demote to admin
                                </button>
                              ) : null}
                            </>
                          ) : null}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    
  );
}
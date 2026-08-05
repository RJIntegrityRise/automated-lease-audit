"use client";

import { Laptop, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useSyncExternalStore } from "react";

function subscribe() {
  return () => {};
}

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  const mounted = useSyncExternalStore(
    subscribe,
    () => true,
    () => false,
  );

  if (!mounted) {
    return <div className="h-9 w-28" aria-hidden="true" />;
  }

  const buttonClass = (value: string) =>
    [
      "rounded-md p-2 transition-colors",
      "hover:bg-muted hover:text-foreground",
      theme === value
        ? "bg-muted text-foreground"
        : "text-muted-foreground",
    ].join(" ");

  return (
    <div className="flex items-center gap-1 rounded-lg border border-border bg-card p-1">
      <button
        type="button"
        onClick={() => setTheme("light")}
        className={buttonClass("light")}
        aria-label="Use light mode"
        title="Light mode"
      >
        <Sun className="h-4 w-4" />
      </button>

      <button
        type="button"
        onClick={() => setTheme("dark")}
        className={buttonClass("dark")}
        aria-label="Use dark mode"
        title="Dark mode"
      >
        <Moon className="h-4 w-4" />
      </button>

      <button
        type="button"
        onClick={() => setTheme("system")}
        className={buttonClass("system")}
        aria-label="Use system mode"
        title="System mode"
      >
        <Laptop className="h-4 w-4" />
      </button>
    </div>
  );
}

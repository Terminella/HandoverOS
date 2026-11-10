"use client";

import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

type Theme = "light" | "dark";
const KEY = "handoveros-theme";

export default function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("light");

  useEffect(() => {
    setTheme(document.documentElement.dataset.theme === "dark" ? "dark" : "light");
  }, []);

  function apply(next: Theme) {
    setTheme(next);
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem(KEY, next);
    } catch {
      /* storage unavailable: the theme still applies for this visit */
    }
  }

  return (
    <div className="theme-toggle" role="group" aria-label="Colour theme">
      <button type="button" aria-pressed={theme === "light"} aria-label="Light theme" onClick={() => apply("light")}>
        <Sun size={16} aria-hidden="true" />
      </button>
      <button type="button" aria-pressed={theme === "dark"} aria-label="Dark theme" onClick={() => apply("dark")}>
        <Moon size={16} aria-hidden="true" />
      </button>
    </div>
  );
}

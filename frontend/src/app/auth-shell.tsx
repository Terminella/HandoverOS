"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import MobileNav from "../components/layout/MobileNav";
import Sidebar from "../components/layout/Sidebar";
import Topbar from "../components/layout/Topbar";
import { apiRequest } from "../lib/api";
import { getStoredToken } from "../lib/api";
import { clearToken } from "../lib/auth";
import type { BackendProject, CurrentUser, Project } from "../lib/types";
import { mapBackendProject } from "../lib/types";
import "./globals.css";

const AUTH_PATHS = ["/login", "/register"];

export default function AuthShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const isAuthPath = AUTH_PATHS.includes(pathname);
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    const token = getStoredToken();

    if (!token) {
      setLoading(false);
      return;
    }

    async function loadUserData() {
      try {
        const [profile, backendProjects] = await Promise.all([
          apiRequest<CurrentUser>("/users/me", getStoredToken() ?? undefined),
          apiRequest<BackendProject[]>("/projects", getStoredToken() ?? undefined),
        ]);
        if (mounted) {
          setUser(profile);
          setProjects(backendProjects.map(mapBackendProject));
        }
      } catch {
        if (mounted) {
          clearToken();
          window.location.replace("/login");
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }

    loadUserData();
    return () => { mounted = false; };
  }, []);

  const userForDisplay = user
    ? {
        name: user.name,
        initials: user.name
          .split(" ")
          .map((part) => part[0])
          .join("")
          .toUpperCase()
          .slice(0, 2),
      }
    : { name: "User", initials: "U" };

  if (loading) {
    return (
      <div className={isAuthPath ? "shell-auth" : "shell"}>
        <main className="auth-outlet">
          <div className="card placeholder">
            <h1 className="card-title">Loading session…</h1>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className={isAuthPath ? "shell-auth" : "shell"}>
      {!isAuthPath ? (
        <>
          <Sidebar />
          <div className="main">
            <Topbar projects={projects} user={userForDisplay} />
            <main className="content">{children}</main>
          </div>
          <MobileNav />
        </>
      ) : (
        <main className="auth-outlet">{children}</main>
      )}
    </div>
  );
}

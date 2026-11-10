import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import MobileNav from "../components/layout/MobileNav";
import Sidebar from "../components/layout/Sidebar";
import Topbar from "../components/layout/Topbar";
import { projects, user } from "../lib/mock-data";
import "./globals.css";

export const metadata: Metadata = {
  title: "HandoverOS",
  description: "Preserve Knowledge. Maintain Continuity. Empower What Comes Next.",
};

export const viewport: Viewport = { width: "device-width", initialScale: 1, viewportFit: "cover" };

// Runs before first paint so the saved (or system) theme is applied without a flash.
const themeInit = `try{var t=localStorage.getItem("handoveros-theme");if(!t){t=window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"}document.documentElement.dataset.theme=t}catch(e){}`;

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInit }} />
      </head>
      <body>
        <div className="shell">
          <Sidebar />
          <div className="main">
            <Topbar projects={projects} user={user} />
            <main className="content">{children}</main>
          </div>
        </div>
        <MobileNav />
      </body>
    </html>
  );
}

import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import AuthShell from "./auth-shell";

export const metadata: Metadata = {
  title: "HandoverOS",
  description: "Preserve Knowledge. Maintain Continuity. Empower What Comes Next.",
};

export const viewport: Viewport = { width: "device-width", initialScale: 1, viewportFit: "cover" };

const themeInit = `try{var t=localStorage.getItem("handoveros-theme");if(!t){t=window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"}document.documentElement.dataset.theme=t}catch(e){}`;

const authInit = `(()=>{const p=window.location.pathname;const t=localStorage.getItem("handoveros-token");if(p==="/login"&&t){window.location.replace("/");}else if(p!=="/login"&&p!=="/register"&&!t){window.location.replace("/login");}})();`;

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInit }} />
        <script dangerouslySetInnerHTML={{ __html: authInit }} />
      </head>
      <body>
        <AuthShell>{children}</AuthShell>
      </body>
    </html>
  );
}

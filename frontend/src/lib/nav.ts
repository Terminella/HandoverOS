import { Database, FileText, Home, Layers, Settings, Sparkles, Users } from "lucide-react";

export const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: Home },
  { href: "/projects", label: "Projects", icon: Layers },
  { href: "/sources", label: "Sources", icon: Database },
  { href: "/intelligence", label: "Intelligence", icon: Sparkles },
  { href: "/handovers", label: "Handovers", icon: FileText },
  { href: "/team", label: "Team", icon: Users },
  { href: "/settings", label: "Settings", icon: Settings },
] as const;

/** Bottom bar on small screens (matches the mobile design). */
export const MOBILE_NAV_HREFS: string[] = ["/", "/projects", "/sources", "/intelligence", "/handovers"];
export const MOBILE_MORE_NAV_HREFS: string[] = ["/team", "/settings"];

export function isActive(pathname: string, href: string): boolean {
  return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(href + "/");
}

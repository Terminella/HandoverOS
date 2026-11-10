"use client";

import { Leaf } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { NAV_ITEMS, isActive } from "../../lib/nav";
import ThemeToggle from "./ThemeToggle";

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="sidebar">
      <Link href="/" className="brand">
        <Leaf size={28} aria-hidden="true" />
        <span>HandoverOS</span>
      </Link>
      <nav aria-label="Main">
        <ul className="nav-list">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => (
            <li key={href}>
              <Link href={href} className="nav-link" aria-current={isActive(pathname, href) ? "page" : undefined}>
                <Icon size={20} aria-hidden="true" />
                {label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
      <div className="sidebar-foot">
        <span>Theme</span>
        <ThemeToggle />
      </div>
    </aside>
  );
}

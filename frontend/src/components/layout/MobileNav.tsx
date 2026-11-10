"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { MOBILE_NAV_HREFS, NAV_ITEMS, isActive } from "../../lib/nav";

export default function MobileNav() {
  const pathname = usePathname();
  const items = NAV_ITEMS.filter((i) => MOBILE_NAV_HREFS.includes(i.href));
  return (
    <nav className="mobile-nav" aria-label="Main">
      {items.map(({ href, label, icon: Icon }) => (
        <Link key={href} href={href} aria-current={isActive(pathname, href) ? "page" : undefined}>
          <Icon size={22} aria-hidden="true" />
          {label}
        </Link>
      ))}
    </nav>
  );
}

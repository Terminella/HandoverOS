"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { MoreHorizontal } from "lucide-react";
import { useEffect, useState } from "react";
import { MOBILE_MORE_NAV_HREFS, MOBILE_NAV_HREFS, NAV_ITEMS, isActive } from "../../lib/nav";

export default function MobileNav() {
  const pathname = usePathname();
  const [moreOpen, setMoreOpen] = useState(false);
  const items = NAV_ITEMS.filter((item) => MOBILE_NAV_HREFS.includes(item.href));
  const moreItems = NAV_ITEMS.filter((item) => MOBILE_MORE_NAV_HREFS.includes(item.href));

  useEffect(() => {
    setMoreOpen(moreItems.some((item) => isActive(pathname, item.href)));
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMoreOpen(false);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [pathname]);

  return (
    <nav className="mobile-nav" aria-label="Main">
      {items.map(({ href, label, icon: Icon }) => (
        <Link key={href} href={href} aria-current={isActive(pathname, href) ? "page" : undefined}>
          <Icon size={22} aria-hidden="true" />
          {label}
        </Link>
      ))}
      <div className="mobile-nav-more">
        <button
          type="button"
          className="mobile-nav-more-toggle"
          aria-expanded={moreOpen}
          aria-haspopup="menu"
          aria-label="More navigation options"
          onClick={() => setMoreOpen((open) => !open)}
        >
          <MoreHorizontal size={22} aria-hidden="true" />
          More
        </button>
        {moreOpen ? (
          <div className="mobile-nav-menu" role="menu">
            {moreItems.map(({ href, label, icon: Icon }) => (
              <Link key={href} href={href} role="menuitem" aria-current={isActive(pathname, href) ? "page" : undefined} onClick={() => setMoreOpen(false)}>
                <Icon size={18} aria-hidden="true" />
                {label}
              </Link>
            ))}
          </div>
        ) : null}
      </div>
    </nav>
  );
}

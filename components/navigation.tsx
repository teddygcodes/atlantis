"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { NAV_ITEMS } from "@/lib/data";

const ROUTE_MAP: Record<string, string> = {
  Chronicle: "/chronicle",
  States: "/states",
  Archive: "/archive",
  Debates: "/debates",
  Graveyard: "/graveyard",
  About: "/about",
};

export function Navigation() {
  const pathname = usePathname();

  const activeItem = NAV_ITEMS.find(
    (item) => ROUTE_MAP[item] === pathname
  );

  return (
    <header className="nav-animate-in sticky top-0 z-50 border-b border-border/50 bg-background/90 backdrop-blur-md">
      <nav className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
        <Link
          href="/"
          className="flex items-center gap-2.5 transition-opacity hover:opacity-70"
          aria-label="Go home"
        >
          <Image
            src="/images/logo.png"
            alt="Atlantis logo"
            width={20}
            height={20}
            className="object-contain"
            style={{ width: "20px", height: "auto" }}
          />
          <span
            className="text-[10px] tracking-[0.3em] text-foreground"
            style={{ fontFamily: "var(--font-cinzel)" }}
          >
            ATLANTIS
          </span>
        </Link>

        <div className="hidden items-center gap-6 md:flex">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item}
              href={ROUTE_MAP[item] || "/"}
              className={`relative py-1 text-[10px] uppercase tracking-[0.15em] transition-colors ${
                activeItem === item
                  ? "text-foreground"
                  : "text-muted/40 hover:text-muted"
              }`}
              style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
            >
              {item}
              {activeItem === item && (
                <span className="absolute -bottom-[17px] left-0 right-0 h-px bg-accent" />
              )}
            </Link>
          ))}
        </div>

        {/* Mobile */}
        <div className="md:hidden">
          <select
            value={activeItem || ""}
            onChange={(e) => {
              const href = ROUTE_MAP[e.target.value];
              if (href) window.location.href = href;
            }}
            className="rounded border border-border bg-background px-3 py-2 text-[10px] uppercase tracking-[0.15em] text-foreground"
            style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
            aria-label="Navigation"
          >
            {NAV_ITEMS.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </div>
      </nav>
    </header>
  );
}

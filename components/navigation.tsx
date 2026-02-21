"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { NAV_ITEMS } from "@/lib/data";

const ROUTE_MAP: Record<string, string> = {
  "Research Timeline": "/chronicle",
  States: "/states",
  "Knowledge Base": "/archive",
  Debates: "/debates",
  Refuted: "/graveyard",
  About: "/about",
};

export function Navigation() {
  const pathname = usePathname();

  const activeItem = NAV_ITEMS.find(
    (item) => {
      const route = ROUTE_MAP[item];
      return route && (pathname === route || pathname.startsWith(route + "/"));
    }
  );

  return (
    <header
      className="sticky top-0 z-50"
      style={{ height: "64px", backgroundColor: "#060606", borderBottom: "1px solid #1a1a1a" }}
    >
      <nav className="mx-auto flex h-full max-w-6xl items-center px-6">
        {/* Logo home link */}
        <Link
          href="/"
          className="flex-shrink-0 transition-opacity hover:opacity-70"
          aria-label="Go home"
        >
          <Image
            src="/images/logo.png"
            alt="Atlantis logo"
            width={56}
            height={56}
            className="object-contain"
            style={{ width: "56px", height: "56px" }}
          />
        </Link>

        {/* Centered nav links */}
        <div className="hidden flex-1 items-center justify-center gap-8 md:flex">
          {NAV_ITEMS.map((item) => {
            const isActive = activeItem === item;
            return (
              <Link
                key={item}
                href={ROUTE_MAP[item] || "/"}
                className="relative py-1 transition-colors duration-200"
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "11px",
                  textTransform: "uppercase" as const,
                  letterSpacing: "0.15em",
                  color: isActive ? "#dc2626" : "#e5e5e5",
                }}
                onMouseEnter={(e) => {
                  if (!isActive) e.currentTarget.style.color = "#a3a3a3";
                }}
                onMouseLeave={(e) => {
                  if (!isActive) e.currentTarget.style.color = "#e5e5e5";
                }}
              >
                {item}
              </Link>
            );
          })}
        </div>

        {/* Mobile nav */}
        <div className="ml-auto md:hidden">
          <select
            value={activeItem || ""}
            onChange={(e) => {
              const href = ROUTE_MAP[e.target.value];
              if (href) window.location.href = href;
            }}
            className="rounded border border-border bg-background px-3 py-2 text-foreground"
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "11px",
              textTransform: "uppercase" as const,
              letterSpacing: "0.15em",
            }}
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

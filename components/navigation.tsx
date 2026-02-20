"use client";

import Image from "next/image";
import { NAV_ITEMS, type NavItem } from "@/lib/data";

interface NavigationProps {
  activeTab: NavItem;
  onTabChange: (tab: NavItem) => void;
}

export function Navigation({ activeTab, onTabChange }: NavigationProps) {
  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur-sm">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <button
          onClick={() => onTabChange("Chronicle")}
          className="flex items-center gap-3 transition-opacity hover:opacity-80"
          aria-label="Go to Chronicle"
        >
          <Image
            src="/images/logo.png"
            alt="Atlantis logo"
            width={40}
            height={40}
            className="object-contain"
          />
          <span
            className="font-[var(--font-cinzel)] text-lg tracking-[0.3em] text-foreground"
            style={{ fontFamily: "var(--font-cinzel)" }}
          >
            ATLANTIS
          </span>
        </button>

        <div className="hidden items-center gap-1 md:flex">
          {NAV_ITEMS.map((item) => (
            <button
              key={item}
              onClick={() => onTabChange(item)}
              className={`relative px-3 py-2 text-sm transition-colors ${
                activeTab === item
                  ? "font-semibold text-foreground"
                  : "text-muted hover:text-foreground"
              }`}
              style={{ fontFamily: "var(--font-cinzel)" }}
            >
              {item}
              {activeTab === item && (
                <span className="absolute bottom-0 left-3 right-3 h-0.5 bg-accent" />
              )}
            </button>
          ))}
        </div>

        <MobileMenu activeTab={activeTab} onTabChange={onTabChange} />
      </nav>
    </header>
  );
}

function MobileMenu({
  activeTab,
  onTabChange,
}: {
  activeTab: NavItem;
  onTabChange: (tab: NavItem) => void;
}) {
  return (
    <div className="md:hidden">
      <select
        value={activeTab}
        onChange={(e) => onTabChange(e.target.value as NavItem)}
        className="rounded border border-border bg-surface px-3 py-2 text-sm text-foreground"
        style={{ fontFamily: "var(--font-cinzel)" }}
        aria-label="Navigation"
      >
        {NAV_ITEMS.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>
    </div>
  );
}

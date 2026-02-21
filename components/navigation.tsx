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
      <nav className="mx-auto flex max-w-5xl items-center justify-between px-6 py-5">
        <button
          onClick={() => onTabChange("Chronicle")}
          className="flex items-center gap-2.5 transition-opacity hover:opacity-80"
          aria-label="Go to Chronicle"
        >
          <Image
            src="/images/logo.png"
            alt="Atlantis logo"
            width={24}
            height={24}
            className="object-contain"
            style={{ width: "24px", height: "auto" }}
          />
          <span
            className="text-sm tracking-[0.3em] text-foreground"
            style={{ fontFamily: "var(--font-cinzel)" }}
          >
            ATLANTIS
          </span>
        </button>

        <div className="hidden items-center gap-6 md:flex">
          {NAV_ITEMS.map((item) => (
            <button
              key={item}
              onClick={() => onTabChange(item)}
              className={`relative py-1 text-[11px] uppercase tracking-[0.15em] transition-colors ${
                activeTab === item
                  ? "text-foreground"
                  : "text-muted hover:text-foreground"
              }`}
              style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
            >
              {item}
              {activeTab === item && (
                <span className="absolute -bottom-[21px] left-0 right-0 h-px bg-accent" />
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
        className="rounded border border-border bg-surface px-3 py-2 text-[11px] uppercase tracking-[0.15em] text-foreground"
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
  );
}

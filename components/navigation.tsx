"use client";

import Image from "next/image";
import { NAV_ITEMS, type NavItem } from "@/lib/data";

interface NavigationProps {
  activeTab: NavItem;
  onTabChange: (tab: NavItem) => void;
  visible: boolean;
  onHome?: () => void;
}

export function Navigation({ activeTab, onTabChange, visible, onHome }: NavigationProps) {
  if (!visible) return null;

  return (
    <header className="nav-animate-in sticky top-0 z-50 border-b border-border/50 bg-background/90 backdrop-blur-md">
      <nav className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
        <button
          onClick={onHome ?? (() => onTabChange("Chronicle"))}
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
        </button>

        <div className="hidden items-center gap-6 md:flex">
          {NAV_ITEMS.map((item) => (
            <button
              key={item}
              onClick={() => onTabChange(item)}
              className={`relative py-1 text-[10px] uppercase tracking-[0.15em] transition-colors ${
                activeTab === item
                  ? "text-foreground"
                  : "text-muted/40 hover:text-muted"
              }`}
              style={{ fontFamily: "var(--font-ibm-plex-mono)" }}
            >
              {item}
              {activeTab === item && (
                <span className="absolute -bottom-[17px] left-0 right-0 h-px bg-accent" />
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
  );
}

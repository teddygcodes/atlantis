"use client";

import { useState, useRef, useEffect } from "react";
import { Navigation } from "@/components/navigation";
import { HeroLogo } from "@/components/hero-logo";
import { SectionGrid } from "@/components/section-grid";
import { Chronicle } from "@/components/chronicle";
import { States } from "@/components/states";
import { Archive } from "@/components/archive";
import { Debates } from "@/components/debates";
import { Graveyard } from "@/components/graveyard";
import { About } from "@/components/about";
import type { NavItem } from "@/lib/data";

export default function Home() {
  const [activeSection, setActiveSection] = useState<NavItem | null>(null);
  const [enteredWorld, setEnteredWorld] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);

  const handleEnter = () => {
    setEnteredWorld(true);
  };

  // Detect scroll past hero to auto-enter
  useEffect(() => {
    if (enteredWorld) return;
    const handleScroll = () => {
      if (window.scrollY > window.innerHeight * 0.5) {
        setEnteredWorld(true);
      }
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, [enteredWorld]);

  const handleNavigate = (tab: NavItem) => {
    setActiveSection(tab);
    setEnteredWorld(true);
    setTimeout(() => {
      contentRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 50);
  };

  const handleBackToGrid = () => {
    setActiveSection(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="min-h-screen">
      {/* Full-screen hero -- always present at top */}
      <HeroLogo onEnter={handleEnter} />

      {/* Section grid -- the primary navigation tiles */}
      {!activeSection && <SectionGrid onNavigate={handleNavigate} />}

      {/* Active section content */}
      {activeSection && (
        <>
          <Navigation
            activeTab={activeSection}
            onTabChange={handleNavigate}
            visible={true}
            onHome={handleBackToGrid}
          />

          <div ref={contentRef}>
            {activeSection === "Chronicle" && (
              <main className="px-4 py-24 md:py-32">
                <Chronicle />
              </main>
            )}

            {activeSection !== "Chronicle" && (
              <main className="mx-auto max-w-5xl px-6 py-20 md:py-32">
                {activeSection === "States" && <States />}
                {activeSection === "Archive" && <Archive />}
                {activeSection === "Debates" && <Debates />}
                {activeSection === "Graveyard" && <Graveyard />}
                {activeSection === "About" && <About />}
              </main>
            )}
          </div>
        </>
      )}
    </div>
  );
}

"use client";

import { useState, useRef, useEffect } from "react";
import { Navigation } from "@/components/navigation";
import { HeroLogo } from "@/components/hero-logo";
import { Chronicle } from "@/components/chronicle";
import { States } from "@/components/states";
import { Archive } from "@/components/archive";
import { Debates } from "@/components/debates";
import { Graveyard } from "@/components/graveyard";
import { About } from "@/components/about";
import type { NavItem } from "@/lib/data";

export default function Home() {
  const [activeTab, setActiveTab] = useState<NavItem>("Chronicle");
  const [enteredWorld, setEnteredWorld] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);

  const handleEnter = () => {
    setEnteredWorld(true);
    setTimeout(() => {
      contentRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 100);
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

  const handleTabChange = (tab: NavItem) => {
    setActiveTab(tab);
    if (contentRef.current) {
      contentRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div className="min-h-screen">
      {/* Full-screen hero */}
      {activeTab === "Chronicle" && <HeroLogo onEnter={handleEnter} />}

      {/* Navigation appears after entering */}
      <Navigation
        activeTab={activeTab}
        onTabChange={handleTabChange}
        visible={enteredWorld || activeTab !== "Chronicle"}
      />

      {/* Content area */}
      <div ref={contentRef}>
        {activeTab === "Chronicle" && (
          <main className="px-4 py-24 md:py-32">
            <Chronicle />
          </main>
        )}

        {activeTab !== "Chronicle" && (
          <main className="mx-auto max-w-5xl px-6 py-20 md:py-32">
            {activeTab === "States" && <States />}
            {activeTab === "Archive" && <Archive />}
            {activeTab === "Debates" && <Debates />}
            {activeTab === "Graveyard" && <Graveyard />}
            {activeTab === "About" && <About />}
          </main>
        )}
      </div>
    </div>
  );
}

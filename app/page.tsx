"use client";

import { useState } from "react";
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

  const handleTabChange = (tab: NavItem) => {
    setActiveTab(tab);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="min-h-screen">
      <Navigation activeTab={activeTab} onTabChange={handleTabChange} />

      {activeTab === "Chronicle" && (
        <>
          <HeroLogo />
          <main className="mx-auto max-w-5xl px-6 pb-32">
            <Chronicle />
          </main>
        </>
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
  );
}

"use client";

import { useState, useEffect } from "react";
import { HeroLogo } from "@/components/hero-logo";
import { SectionGrid } from "@/components/section-grid";

export default function Home() {
  const [enteredWorld, setEnteredWorld] = useState(false);

  const handleEnter = () => {
    setEnteredWorld(true);
  };

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

  return (
    <div className="min-h-screen" /* refreshed */>
      <HeroLogo onEnter={handleEnter} />
      <SectionGrid />
    </div>
  );
}

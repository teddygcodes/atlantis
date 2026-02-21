"use client";

import Image from "next/image";

export function HeroLogo() {
  return (
    <section className="flex flex-col items-center justify-center px-6 pb-24 pt-20 md:pb-32 md:pt-28">
      <div className="animate-fade-in-up mb-8">
        <Image
          src="/images/logo.png"
          alt="Atlantis logo"
          width={140}
          height={140}
          className="object-contain"
          style={{ width: "140px", height: "auto" }}
          priority
        />
      </div>
      <h1
        className="animate-fade-in-up animation-delay-200 mb-6 text-center text-2xl tracking-[0.35em] text-foreground md:text-3xl"
        style={{ fontFamily: "var(--font-cinzel)" }}
      >
        ATLANTIS
      </h1>
      <p
        className="animate-fade-in-up animation-delay-300 max-w-md text-center text-[18px] leading-[1.9] text-muted"
        style={{ fontFamily: "var(--font-cormorant)" }}
      >
        Where ideas are tested. Only validated knowledge survives.
      </p>
      <div
        className="animate-fade-in-up animation-delay-400 mt-16 h-px w-12"
        style={{ backgroundColor: "#dc2626" }}
      />
    </section>
  );
}

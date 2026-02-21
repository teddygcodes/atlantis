"use client";

import { useEffect, useRef, useCallback } from "react";
import Image from "next/image";

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  opacity: number;
  pulse: number;
  pulseSpeed: number;
}

function ParticleField() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);
  const animationRef = useRef<number>(0);
  const mouseRef = useRef({ x: -1000, y: -1000 });

  const initParticles = useCallback((width: number, height: number) => {
    const count = Math.floor((width * height) / 12000);
    particlesRef.current = Array.from({ length: Math.min(count, 120) }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.15,
      vy: (Math.random() - 0.5) * 0.15,
      size: Math.random() * 1.5 + 0.5,
      opacity: Math.random() * 0.4 + 0.1,
      pulse: Math.random() * Math.PI * 2,
      pulseSpeed: Math.random() * 0.01 + 0.005,
    }));
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const resize = () => {
      const dpr = window.devicePixelRatio || 1;
      canvas.width = window.innerWidth * dpr;
      canvas.height = window.innerHeight * dpr;
      canvas.style.width = `${window.innerWidth}px`;
      canvas.style.height = `${window.innerHeight}px`;
      ctx.scale(dpr, dpr);
      initParticles(window.innerWidth, window.innerHeight);
    };
    resize();
    window.addEventListener("resize", resize);

    const handleMouse = (e: MouseEvent) => {
      mouseRef.current = { x: e.clientX, y: e.clientY };
    };
    window.addEventListener("mousemove", handleMouse);

    const animate = () => {
      const w = window.innerWidth;
      const h = window.innerHeight;
      ctx.clearRect(0, 0, w, h);

      const particles = particlesRef.current;
      const mouse = mouseRef.current;

      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        p.pulse += p.pulseSpeed;

        if (p.x < 0) p.x = w;
        if (p.x > w) p.x = 0;
        if (p.y < 0) p.y = h;
        if (p.y > h) p.y = 0;

        const dx = mouse.x - p.x;
        const dy = mouse.y - p.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 150) {
          const force = (150 - dist) / 150;
          p.vx -= (dx / dist) * force * 0.02;
          p.vy -= (dy / dist) * force * 0.02;
        }

        p.vx *= 0.99;
        p.vy *= 0.99;

        const pulseOpacity = p.opacity + Math.sin(p.pulse) * 0.15;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(220, 38, 38, ${Math.max(0.03, pulseOpacity)})`;
        ctx.fill();
      }

      // Draw connections
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 100) {
            const opacity = (1 - dist / 100) * 0.06;
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(220, 38, 38, ${opacity})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
      }

      animationRef.current = requestAnimationFrame(animate);
    };
    animate();

    return () => {
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", handleMouse);
      cancelAnimationFrame(animationRef.current);
    };
  }, [initParticles]);

  return (
    <canvas
      ref={canvasRef}
      className="pointer-events-none absolute inset-0"
      aria-hidden="true"
    />
  );
}

export function HeroLogo({ onEnter }: { onEnter: () => void }) {
  const heroRef = useRef<HTMLDivElement>(null);

  return (
    <section
      ref={heroRef}
      className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden"
    >
      <ParticleField />

      <div className="relative z-10 flex flex-col items-center justify-between px-6" style={{ minHeight: "100vh" }}>
        {/* Top: Logo pushed toward upper portion */}
        <div className="flex flex-1 items-end pb-4 pt-12 hero-fade-in">
          <Image
            src="/images/hero-emblem.png"
            alt="Atlantis logo"
            width={560}
            height={560}
            className="object-contain drop-shadow-[0_0_100px_rgba(220,38,38,0.3)]"
            style={{ width: "min(560px, 80vw)", height: "auto", maxWidth: "100%" }}
            priority
            crossOrigin="anonymous"
          />
        </div>

        {/* Middle: Wordmark + three lines */}
        <div className="flex flex-col items-center">
          <h1
            className="hero-fade-in-delay-1 text-center tracking-[0.3em] text-foreground"
            style={{ fontFamily: "var(--font-cinzel)", fontSize: "clamp(48px, 8vw, 72px)" }}
          >
            ATLANTIS
          </h1>

          <div
            className="hero-fade-in-delay-2 mt-6 mb-6 h-px w-20"
            style={{ backgroundColor: "rgba(220, 38, 38, 0.5)" }}
          />

          <div className="hero-fade-in-delay-2 flex flex-col items-center gap-2">
            <p
              className="text-center"
              style={{ fontFamily: "var(--font-cormorant)", fontSize: "20px", color: "#a3a3a3" }}
            >
              Hypotheses are proposed.
            </p>
            <p
              className="text-center"
              style={{ fontFamily: "var(--font-cormorant)", fontSize: "20px", color: "#a3a3a3" }}
            >
              Peer review is conducted.
            </p>
            <p
              className="text-center"
              style={{ fontFamily: "var(--font-cormorant)", fontSize: "20px", color: "#a3a3a3" }}
            >
              Only validated knowledge survives.
            </p>
          </div>
        </div>

        {/* Bottom: Scroll prompt */}
        <div className="flex flex-1 items-start pt-6 pb-16">
          <button
            onClick={onEnter}
            className="hero-fade-in-delay-3 group flex flex-col items-center gap-2 transition-opacity hover:opacity-70"
            aria-label="Enter Atlantis"
          >
            <span
              className="text-[10px] uppercase tracking-[0.3em]"
              style={{ fontFamily: "var(--font-ibm-plex-mono)", color: "rgba(163,163,163,0.5)" }}
            >
              Scroll to enter
            </span>
            <svg
              width="16"
              height="24"
              viewBox="0 0 16 24"
              fill="none"
              className="animate-gentle-bounce"
              style={{ color: "rgba(163,163,163,0.35)" }}
            >
              <path
                d="M8 0v20m0 0l-6-6m6 6l6-6"
                stroke="currentColor"
                strokeWidth="1"
              />
            </svg>
          </button>
        </div>
      </div>
    </section>
  );
}

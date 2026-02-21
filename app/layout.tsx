import type { Metadata, Viewport } from "next";
import { Cinzel, Cormorant_Garamond, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";

const cinzel = Cinzel({
  subsets: ["latin"],
  variable: "--font-cinzel",
  display: "swap",
});

const cormorant = Cormorant_Garamond({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-cormorant",
  display: "swap",
});

const ibmPlexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-ibm-plex-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ATLANTIS \u2014 Where Ideas Are Tested",
  description:
    "A living research platform where hypotheses are challenged through structured adversarial review. Only validated knowledge survives.",
};

export const viewport: Viewport = {
  themeColor: "#060606",
};

export default function RootLayout /* v2.1 */ ({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${cinzel.variable} ${cormorant.variable} ${ibmPlexMono.variable}`}
    >
      <body className="min-h-screen bg-background text-foreground antialiased">
        {children}
        <footer
          style={{
            textAlign: "center",
            padding: "40px 0 32px",
            fontFamily: "var(--font-ibm-plex-mono)",
            fontSize: "11px",
            letterSpacing: "0.2em",
            color: "#525252",
          }}
        >
          ATLANTIS v2.1
        </footer>
      </body>
    </html>
  );
}

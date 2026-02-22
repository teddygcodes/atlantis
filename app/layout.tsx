import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ATLANTIS \u2014 Where Ideas Are Tested",
  description:
    "A living research platform where hypotheses are challenged through structured adversarial review. Only validated knowledge survives.",
};

export const viewport: Viewport = {
  themeColor: "#060606",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
    >
      <body className="min-h-screen bg-background text-foreground antialiased">
        {children}
        <footer
          className="footer-links"
          style={{
            textAlign: "center",
            padding: "40px 0 32px",
            fontFamily: "var(--font-ibm-plex-mono)",
            fontSize: "11px",
            letterSpacing: "0.2em",
            color: "#525252",
          }}
        >
          <span>ATLANTIS v2.2</span>
          <span style={{ color: "#525252" }}>{" · "}</span>
          <a
            href="https://atlantiskb.com"
            target="_blank"
            rel="noopener noreferrer"
          >
            atlantiskb.com
          </a>
          <span style={{ color: "#525252" }}>{" · "}</span>
          <a
            href="https://github.com/teddygcodes/atlantis"
            target="_blank"
            rel="noopener noreferrer"
          >
            GitHub
          </a>
        </footer>
      </body>
    </html>
  );
}

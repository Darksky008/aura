import type { Metadata, Viewport } from "next";
import { ToastProvider } from "@/components/ui/Toast";
import "./globals.css";

export const metadata: Metadata = {
  title: "AURA - AI Dining Concierge | Aurelia Grand Hotel",
  description: "A voice-first digital dining concierge for hotel restaurants. Ask about the menu, ingredients, allergens and chef specials in English, Tamil or Hindi.",
};
export const viewport: Viewport = { themeColor: "#0B0910", width: "device-width", initialScale: 1 };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        {/* Latin display + UI faces, plus Tamil and Devanagari so every language renders crisply */}
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,500&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Noto+Sans+Tamil:wght@400;500;600&family=Noto+Sans+Devanagari:wght@400;500;600&family=Noto+Serif+Tamil:wght@500;600&family=Noto+Serif+Devanagari:wght@500;600&display=swap"
        />
      </head>
      <body>
        <ToastProvider>{children}</ToastProvider>
      </body>
    </html>
  );
}

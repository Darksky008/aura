import type { Config } from "tailwindcss";

/** "Saffron Noir" - warm ink surfaces, brass + saffron accents, ivory type. */
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: { DEFAULT: "#0B0910", 2: "#120F18", 3: "#1A1622" },
        ivory: { DEFAULT: "#F4EEE2", dim: "#CFC7B8" },
        muted: "#A39DB0",
        gold: { DEFAULT: "#D9AE5B", soft: "#EBD3A0", deep: "#A9812F" },
        saffron: { DEFAULT: "#E8843F", deep: "#C4552D" },
        jade: "#5FC7A1",
        rose: "#E5707A",
      },
      fontFamily: {
        display: ['"Cormorant Garamond"', '"Noto Serif Tamil"', '"Noto Serif Devanagari"', "Georgia", "serif"],
        sans: ['"Plus Jakarta Sans"', '"Noto Sans Tamil"', '"Noto Sans Devanagari"', "system-ui", "sans-serif"],
      },
      boxShadow: {
        glass: "0 1px 0 rgba(255,255,255,0.06) inset, 0 24px 60px -24px rgba(0,0,0,0.7)",
        glow: "0 0 80px -10px rgba(232,132,63,0.35)",
      },
      keyframes: {
        drift: { "0%,100%": { transform: "translate3d(0,0,0) scale(1)" }, "50%": { transform: "translate3d(2%,-3%,0) scale(1.06)" } },
        pulseRing: { "0%": { transform: "scale(0.9)", opacity: "0.55" }, "100%": { transform: "scale(1.35)", opacity: "0" } },
        rise: { from: { opacity: "0", transform: "translateY(10px)" }, to: { opacity: "1", transform: "translateY(0)" } },
        bar: { "0%,100%": { transform: "scaleY(0.35)" }, "50%": { transform: "scaleY(1)" } },
        shimmer: { "0%": { backgroundPosition: "-200% 0" }, "100%": { backgroundPosition: "200% 0" } },
      },
      animation: {
        drift: "drift 14s ease-in-out infinite", pulseRing: "pulseRing 1.8s ease-out infinite", rise: "rise 0.45s cubic-bezier(.2,.8,.2,1) both",
        bar: "bar 0.9s ease-in-out infinite", shimmer: "shimmer 2.4s linear infinite",
      },
    },
  },
  plugins: [],
};
export default config;

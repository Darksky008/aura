import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  turbopack: {
    root: __dirname,
  },
  reactStrictMode: true,
  poweredByHeader: false,
  // The microphone only works on https (Vercel) or localhost. Permissions-Policy allows it for this origin.
  async headers() {
    return [{ source: "/(.*)", headers: [
      { key: "Permissions-Policy", value: "microphone=(self), camera=()" },
      { key: "X-Content-Type-Options", value: "nosniff" },
      { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
    ] }];
  },
};
export default nextConfig;

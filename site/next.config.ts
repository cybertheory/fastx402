import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  /* config options here */
  // Configure Turbopack to resolve path aliases
  turbopack: {
    resolveAlias: {
      "@": path.resolve(__dirname),
    },
  },
};

export default nextConfig;

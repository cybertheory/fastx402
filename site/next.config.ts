import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  /* config options here */
  // Configure Turbopack to resolve @ alias
  turbopack: {
    resolveAlias: {
      "@": path.resolve(process.cwd()),
    },
  },
};

export default nextConfig;

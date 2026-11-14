import type { NextConfig } from "next";

// No custom settings are required by the current source code
// (no remote images, env vars, rewrites or custom webpack config).
const nextConfig: NextConfig = {
  // Allow development server HMR origins for both localhost and 127.0.0.1
  allowedDevOrigins: ["localhost", "127.0.0.1"],
  // Disable the built-in Next.js development runtime error overlay indicator
  devIndicators: false,
};

export default nextConfig;
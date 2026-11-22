import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Automated test runs build into their own directory (NEXT_DIST_DIR=.next-test)
  // so they never collide with a `next dev` server using `.next` (D-35).
  distDir: process.env.NEXT_DIST_DIR || ".next",
};

export default nextConfig;

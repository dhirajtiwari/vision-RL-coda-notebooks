import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: true,
  output: "standalone",
  // Pin tracing root to this folder so standalone output isn't nested under a
  // parent workspace root (repo has multiple lockfiles).
  outputFileTracingRoot: path.join(__dirname),
};

export default nextConfig;

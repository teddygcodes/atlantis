/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  turbopack: {
    resolveAlias: {
      canvas: false,
    },
  },
};

export default nextConfig;

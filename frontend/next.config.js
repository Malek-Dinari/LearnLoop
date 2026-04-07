/** @type {import('next').NextConfig} */
const nextConfig = {
  // Required for the Docker multi-stage build (node server.js)
  output: "standalone",

  async rewrites() {
    // In Docker, BACKEND_INTERNAL_URL points to the backend container.
    // Locally, falls back to localhost:8000.
    const backendUrl = process.env.BACKEND_INTERNAL_URL || "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;

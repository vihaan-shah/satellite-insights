/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "gibs.earthdata.nasa.gov" },
    ],
  },
};

module.exports = nextConfig;

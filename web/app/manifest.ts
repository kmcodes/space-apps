import type { MetadataRoute } from "next";

// Makes the site installable to a phone's home screen (PWA).
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Field Aid",
    short_name: "Field Aid",
    description: "Compare crop rotations for rainfed farms in Vidarbha.",
    start_url: "/",
    display: "standalone",
    background_color: "#f5f5f4",
    theme_color: "#065f46",
    icons: [{ src: "/icon.svg", sizes: "any", type: "image/svg+xml", purpose: "any" }],
  };
}

import type {
  Metadata,
} from "next";

import "./globals.css";
import "leaflet/dist/leaflet.css";


export const metadata: Metadata = {
  title: "Guardian X",
  description:
    "Evidence-first AI telecom intelligence platform",
};


export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}

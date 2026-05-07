import type { Metadata } from "next";
import { Manrope } from "next/font/google";
import "./globals.css";

const manrope = Manrope({
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "PharmaSim — Drug Safety Simulator",
  description:
    "Pre-clinical drug safety simulation. Test any drug before it reaches a patient.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={manrope.className}>
      <body>{children}</body>
    </html>
  );
}

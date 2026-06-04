import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/shared/navbar";
import { Footer } from "@/components/shared/footer";

export const metadata: Metadata = {
  title: "ModelRegression.com — AI Model Performance Tracker",
  description:
    "Independent automated benchmarking of frontier AI models. Track regressions, compare performance, and see which model is best — updated 3x daily.",
  openGraph: {
    title: "ModelRegression.com — AI Model Performance Tracker",
    description:
      "Independent automated benchmarking of frontier AI models. Track regressions, compare performance, and see which model is best.",
    type: "website",
    url: "https://modelregression.com",
  },
  twitter: {
    card: "summary_large_image",
    title: "ModelRegression.com",
    description: "Track frontier AI model performance regressions in real time.",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background antialiased">
        <div className="relative min-h-screen flex flex-col">
          {/* Background effects */}
          <div className="fixed inset-0 bg-grid pointer-events-none" />
          <div className="glow-orb fixed top-[-200px] left-[-200px] w-[600px] h-[600px] bg-green-500/20" />
          <div className="glow-orb fixed bottom-[-200px] right-[-200px] w-[500px] h-[500px] bg-blue-500/20" />
          <div className="glow-orb fixed top-[40%] right-[10%] w-[400px] h-[400px] bg-cyan-500/10" />

          {/* Content */}
          <div className="relative z-10 flex flex-col min-h-screen">
            <Navbar />
            <main className="flex-1">{children}</main>
            <Footer />
          </div>
        </div>
      </body>
    </html>
  );
}

import type { Metadata } from "next";
import { Providers } from "./providers";
import { MedievalSharp, Lato } from "next/font/google";
import { NotificationProvider } from "@/components/NotificationProvider";

const medievalSharp = MedievalSharp({
  subsets: ["latin"],
  weight: ["400"],
  variable: "--font-medievalsharp",
});
const lato = Lato({
  subsets: ["latin"],
  weight: ["400", "700"],
  variable: "--font-lato",
});

export const metadata: Metadata = {
  title: "PromptCraft: Dungeon Delver",
  description: "An AI-powered text adventure game.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${medievalSharp.variable} ${lato.variable}`}>
        <NotificationProvider>
          <Providers>{children}</Providers>
        </NotificationProvider>
      </body>
    </html>
  );
}

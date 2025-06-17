import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/components/auth-provider";
import { VoiceContextProvider } from "@/lib/contexts/VoiceContext";
import { PersonaProvider } from "@/lib/contexts/PersonaContext";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Clone Advisor - AI Document Chat",
  description: "Create AI clones from your documents and chat with them",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <VoiceContextProvider>
          <AuthProvider>
            <PersonaProvider>{children}</PersonaProvider>
          </AuthProvider>
        </VoiceContextProvider>
      </body>
    </html>
  );
}

'use client';

import { Inter } from "next/font/google";
import "../globals.css";
import { AuthProvider } from "@/components/auth-provider";
import { PersonaProvider } from "@/lib/contexts/PersonaContext";
import StudioLayout from "./components/StudioLayout";

const inter = Inter({ subsets: ["latin"] });

export default function CommonLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className={inter.className}>
      <AuthProvider>
        <PersonaProvider>
          <StudioLayout>
            {children}
          </StudioLayout>
        </PersonaProvider>
      </AuthProvider>
    </div>
  );
} 
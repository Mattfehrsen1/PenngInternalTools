'use client';

import { useState, useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import TopBar from './TopBar';
import LeftRail from './LeftRail';

interface StudioLayoutProps {
  children: React.ReactNode;
}

export default function StudioLayout({ children }: StudioLayoutProps) {
  const pathname = usePathname();
  const [isRailCollapsed, setIsRailCollapsed] = useState(false);
  
  // Don't show studio layout on login page
  if (pathname === '/login') {
    return <>{children}</>;
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* TopBar (56px) */}
      <TopBar />
      
      <div className="flex flex-1 overflow-hidden">
        {/* LeftRail (220px when expanded) */}
        <LeftRail 
          collapsed={isRailCollapsed} 
          onToggle={() => setIsRailCollapsed(!isRailCollapsed)} 
        />
        
        {/* PageArea (flex-1) */}
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
} 
'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';

export default function GlobalNavigation() {
  const pathname = usePathname();
  const router = useRouter();
  const [currentSection, setCurrentSection] = useState<'brain' | 'chat'>('brain');

  // Determine current section based on pathname
  useEffect(() => {
    if (pathname?.startsWith('/chat')) {
      setCurrentSection('chat');
    } else if (pathname?.startsWith('/brain')) {
      setCurrentSection('brain');
    }
  }, [pathname]);

  const handleSectionChange = (section: 'brain' | 'chat') => {
    setCurrentSection(section);
    router.push(`/${section}`);
  };

  // Don't show navigation on login page
  if (pathname === '/login') {
    return null;
  }

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center">
            <h1 className="text-xl font-bold text-gray-900">Clone Advisor</h1>
          </div>

          {/* Section Toggle */}
          <div className="flex items-center">
            <div className="bg-gray-100 p-1 rounded-lg flex">
              <button
                onClick={() => handleSectionChange('brain')}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                  currentSection === 'brain'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                🧠 Brain
              </button>
              <button
                onClick={() => handleSectionChange('chat')}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                  currentSection === 'chat'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                💬 Chat
              </button>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
} 
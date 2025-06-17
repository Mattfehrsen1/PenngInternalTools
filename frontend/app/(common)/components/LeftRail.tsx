'use client';

import { useState, useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { usePersona } from '@/lib/contexts/PersonaContext';

interface LeftRailProps {
  collapsed: boolean;
  onToggle: () => void;
}

interface NavItem {
  label: string;
  href: string;
  icon: string;
  active?: boolean;
  requiresPersona?: boolean;
}

export default function LeftRail({ collapsed, onToggle }: LeftRailProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { selectedPersona } = usePersona();
  
  // Simplified navigation - only essential features for production
  const navItems: NavItem[] = [
    { label: 'Select Clone', href: '/clones', icon: '🎭' },
    { label: 'Chat', href: '/chat', icon: '💬', requiresPersona: true },
    { label: 'Knowledge Base', href: '/files', icon: '🧠', requiresPersona: true },
    { label: 'Prompts', href: '/prompts', icon: '📝', requiresPersona: true },
  ];

  // Update active states based on current pathname
  const [activeItems, setActiveItems] = useState<NavItem[]>([]);
  
  useEffect(() => {
    setActiveItems(
      navItems.map(item => ({
        ...item,
        active: pathname?.startsWith(item.href) || false
      }))
    );
  }, [pathname]);

  // Handle navigation with persona context
  const handleNavigation = (item: NavItem) => {
    console.log('[LeftRail] Navigation clicked:', item.label, 'requiresPersona:', item.requiresPersona, 'selectedPersona:', selectedPersona?.name);
    
    try {
      if (item.requiresPersona && selectedPersona) {
        const targetUrl = `${item.href}/${selectedPersona.slug || selectedPersona.id}`;
        console.log('[LeftRail] Navigating to:', targetUrl);
        router.push(targetUrl);
      } else if (item.requiresPersona && !selectedPersona) {
        // Redirect to clone selection if none is selected
        console.log('[LeftRail] No clone selected, redirecting to clone selection');
        router.push('/clones');
      } else {
        console.log('[LeftRail] Navigating to:', item.href);
        router.push(item.href);
      }
    } catch (error) {
      console.error('[LeftRail] Navigation error:', error);
      // Fallback to manual navigation
      window.location.href = item.href;
    }
  };

  const railWidth = collapsed ? 'w-12' : 'w-56';
  const railBackground = '#fafafa';
  const activeColor = '#ff7d1a';

  return (
    <div 
      className={`${railWidth} transition-all duration-200 border-r border-gray-200 flex flex-col`}
      style={{ backgroundColor: railBackground }}
    >
      {/* Rail Header */}
      <div className="h-14 border-b border-gray-200 flex items-center justify-between px-3">
        {!collapsed && (
          <div className="flex items-center">
            <span className="text-lg mr-2">🚀</span>
            <span className="text-sm font-bold text-gray-800">Clone Studio</span>
          </div>
        )}
        <button
          onClick={onToggle}
          className="p-1 hover:bg-gray-200 rounded-md transition-colors"
          title={collapsed ? "Expand navigation" : "Collapse navigation"}
        >
          <span className="text-gray-600 text-sm">
            {collapsed ? '→' : '←'}
          </span>
        </button>
      </div>

      {/* Selected Clone Display */}
      {!collapsed && selectedPersona && (
        <div className="px-3 py-3 border-b border-gray-200 bg-gray-100">
          <div className="text-xs font-medium text-gray-500 mb-1">ACTIVE CLONE</div>
          <div className="flex items-center">
            <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center mr-2">
              <span className="text-white text-sm font-bold">
                {selectedPersona.name.charAt(0)}
              </span>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-900">{selectedPersona.name}</div>
              <div className="text-xs text-gray-600">Ready to chat</div>
            </div>
          </div>
        </div>
      )}

      {/* Navigation Items */}
      <div className="flex-1 overflow-y-auto py-4">
        <div className="space-y-1 px-2">
          {activeItems.map((item) => {
            const isDisabled = item.requiresPersona && !selectedPersona;
            
            return (
              <button
                key={item.href}
                onClick={() => {
                  console.log('[LeftRail] Button clicked:', item.label, 'disabled:', isDisabled);
                  if (!isDisabled) {
                    handleNavigation(item);
                  }
                }}
                disabled={isDisabled}
                className={`flex items-center w-full px-3 py-3 text-sm transition-colors rounded-lg ${
                  item.active
                    ? 'text-white font-medium shadow-sm'
                    : isDisabled 
                      ? 'text-gray-400 cursor-not-allowed opacity-50'
                      : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                } ${collapsed ? 'justify-center' : ''}`}
                style={item.active ? { backgroundColor: activeColor } : {}}
                title={collapsed ? item.label : isDisabled ? 'Select a clone first' : undefined}
              >
                <span className={`text-lg mr-3 ${isDisabled ? 'opacity-50' : ''} ${collapsed ? 'mr-0' : ''}`}>
                  {item.icon}
                </span>
                {!collapsed && (
                  <span className={`font-medium ${isDisabled ? 'opacity-50' : ''}`}>
                    {item.label}
                  </span>
                )}
                {!collapsed && isDisabled && (
                  <span className="ml-auto text-xs text-gray-400">
                    ⚠️
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Quick Actions (when not collapsed) */}
      {!collapsed && (
        <div className="border-t border-gray-200 p-3">
          <div className="text-xs font-medium text-gray-500 mb-2">QUICK ACCESS</div>
          <button 
            onClick={() => router.push('/settings')}
            className="flex items-center w-full px-2 py-2 text-xs text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
          >
            <span className="mr-2">⚙️</span>
            Settings
          </button>
        </div>
      )}
    </div>
  );
} 
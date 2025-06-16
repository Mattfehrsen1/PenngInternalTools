'use client';

import { useState, useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { usePersona } from '@/lib/contexts/PersonaContext';
import Link from 'next/link';

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

interface NavSection {
  label: string;
  icon: string;
  items: NavItem[];
  expanded: boolean;
}

export default function LeftRail({ collapsed, onToggle }: LeftRailProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { selectedPersona } = usePersona();
  
  const [sections, setSections] = useState<NavSection[]>([
    {
      label: 'Clones',
      icon: '🎭',
      expanded: true,
      items: [
        { label: 'All Clones', href: '/clones', icon: '📋' },
      ]
    },
    {
      label: 'Communicate',
      icon: '💬',
      expanded: true,
      items: [
        { label: 'Chat', href: '/chat', icon: '💬', requiresPersona: true },
        { label: 'Call', href: '/call', icon: '📞', requiresPersona: true },
        { label: 'Video', href: '/video', icon: '📹', requiresPersona: true },
      ]
    },
    {
      label: 'Workbench',
      icon: '🔧',
      expanded: true,
      items: [
        { label: 'Prompts', href: '/prompts', icon: '📝', requiresPersona: true },
        { label: 'Files', href: '/files', icon: '📁', requiresPersona: true },
        { label: 'Voice', href: '/voice', icon: '🎤', requiresPersona: true },
      ]
    },
    {
      label: 'System',
      icon: '⚙️',
      expanded: false,
      items: [
        { label: 'Quality', href: '/quality', icon: '📊' },
        { label: 'Settings', href: '/settings', icon: '⚙️' },
        { label: 'ChatV2 Demo', href: '/chatv2-demo', icon: '✨' },
      ]
    }
  ]);

  // Update active states based on current pathname
  useEffect(() => {
    setSections(prevSections => 
      prevSections.map(section => ({
        ...section,
        items: section.items.map(item => ({
          ...item,
          active: pathname?.startsWith(item.href) || false
        }))
      }))
    );
  }, [pathname]);

  const toggleSection = (sectionIndex: number) => {
    setSections(prev => 
      prev.map((section, index) => 
        index === sectionIndex 
          ? { ...section, expanded: !section.expanded }
          : section
      )
    );
  };

  // Handle navigation with persona context
  const handleNavigation = (item: NavItem) => {
    if (item.requiresPersona && selectedPersona) {
      router.push(`${item.href}/${selectedPersona.slug}`);
    } else if (item.requiresPersona && !selectedPersona) {
      // Redirect to persona selection if none is selected
      router.push('/clones');
    } else {
      router.push(item.href);
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
          <span className="text-sm font-medium text-gray-700">Navigation</span>
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

      {/* Navigation Sections */}
      <div className="flex-1 overflow-y-auto py-2">
        {sections.map((section, sectionIndex) => (
          <div key={section.label} className="mb-2">
            {/* Section Header */}
            <button
              onClick={() => !collapsed && toggleSection(sectionIndex)}
              className={`w-full flex items-center px-3 py-2 text-left hover:bg-gray-100 transition-colors ${
                collapsed ? 'justify-center' : 'justify-between'
              }`}
              title={collapsed ? section.label : undefined}
            >
              <div className="flex items-center">
                <span className="text-sm mr-2">{section.icon}</span>
                {!collapsed && (
                  <span className="text-sm font-medium text-gray-700">
                    {section.label}
                  </span>
                )}
              </div>
              {!collapsed && (
                <span className="text-xs text-gray-500">
                  {section.expanded ? '▽' : '▷'}
                </span>
              )}
            </button>

            {/* Section Items */}
            {(section.expanded || collapsed) && (
              <div className={collapsed ? 'space-y-1' : 'space-y-0.5 ml-2'}>
                {section.items.map((item) => {
                  const isDisabled = item.requiresPersona && !selectedPersona;
                  
                  return (
                    <button
                      key={item.href}
                      onClick={() => handleNavigation(item)}
                      disabled={isDisabled}
                      className={`flex items-center px-3 py-2 text-sm transition-colors rounded-md mx-2 w-full text-left ${
                        item.active
                          ? 'text-white font-medium'
                          : isDisabled 
                            ? 'text-gray-400 cursor-not-allowed'
                            : 'text-gray-600 hover:bg-gray-100'
                      } ${collapsed ? 'justify-center' : ''}`}
                      style={item.active ? { backgroundColor: activeColor } : {}}
                      title={collapsed ? item.label : isDisabled ? 'Select a persona first' : undefined}
                    >
                      <span className={`text-sm mr-2 ${isDisabled ? 'opacity-50' : ''}`}>
                        {item.icon}
                      </span>
                      {!collapsed && (
                        <span className={isDisabled ? 'opacity-50' : ''}>{item.label}</span>
                      )}
                      {!collapsed && item.requiresPersona && !selectedPersona && (
                        <span className="ml-auto text-xs text-gray-400">📍</span>
                      )}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Rail Footer */}
      {!collapsed && (
        <div className="border-t border-gray-200 p-3">
          <div className="text-xs text-gray-500">
            Sprint 4 UI Revamp
          </div>
          {selectedPersona && (
            <div className="text-xs text-gray-400 mt-1">
              Active: {selectedPersona.name}
            </div>
          )}
        </div>
      )}
    </div>
  );
} 
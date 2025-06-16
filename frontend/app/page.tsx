'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function HomePage() {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    console.log('🏠 Root page: Checking authentication...');
    
    try {
      const token = localStorage.getItem('auth_token');
      console.log('🔍 Token found:', !!token);
      
      if (!token) {
        console.log('❌ No token, redirecting to login');
        router.push('/login');
      } else {
        console.log('✅ Token found, redirecting to brain');
        router.push('/brain');
      }
    } catch (error) {
      console.error('❌ Error checking auth:', error);
      router.push('/login');
    }
    
    // Add a timeout to prevent infinite loading
    const timeout = setTimeout(() => {
      console.log('⏰ Timeout reached, forcing redirect to login');
      router.push('/login');
    }, 3000);

    return () => clearTimeout(timeout);
  }, [router]);

  // Show loading state while checking/redirecting
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Checking authentication...</p>
        <p className="mt-2 text-sm text-gray-500">If this takes too long, click <a href="/login" className="text-blue-600 underline">here</a></p>
      </div>
    </div>
  );
}

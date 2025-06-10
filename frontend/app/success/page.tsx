'use client';

import { useAuth } from '@/components/auth-provider';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function SuccessPage() {
  const { logout } = useAuth();

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-green-600">🎉 Login Successful!</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p>You have successfully logged in to Clone Advisor.</p>
          <div className="flex gap-2">
            <Button 
              onClick={() => window.location.href = '/chat'}
              className="flex-1"
            >
              Go to Chat
            </Button>
            <Button 
              onClick={logout}
              variant="outline"
            >
              Logout
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

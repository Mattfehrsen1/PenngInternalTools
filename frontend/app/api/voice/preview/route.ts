import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization');
    
    if (!authHeader) {
      return NextResponse.json({ error: 'Authorization header required' }, { status: 401 });
    }

    const body = await request.json();

    const response = await fetch(`${BACKEND_URL}/api/voice/preview`, {
      method: 'POST',
      headers: {
        'Authorization': authHeader,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend error:', response.status, errorText);
      return NextResponse.json(
        { error: `Voice preview failed: ${response.status}` }, 
        { status: response.status }
      );
    }

    // For audio responses, we need to handle the binary data
    const contentType = response.headers.get('content-type');
    
    if (contentType && contentType.includes('audio/')) {
      const audioBuffer = await response.arrayBuffer();
      return new NextResponse(audioBuffer, {
        status: 200,
        headers: {
          'Content-Type': contentType,
          'Content-Length': audioBuffer.byteLength.toString(),
        },
      });
    } else {
      // Handle JSON response
      const data = await response.json();
      return NextResponse.json(data);
    }

  } catch (error) {
    console.error('Voice preview API error:', error);
    return NextResponse.json(
      { error: 'Failed to generate voice preview' }, 
      { status: 500 }
    );
  }
} 
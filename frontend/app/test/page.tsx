import { TestButton } from '@/components/test-button';

export default function TestPage() {
  return (
    <div style={{ 
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      backgroundColor: '#dcfce7',
      fontFamily: 'sans-serif'
    }}>
      <div style={{
        background: 'white',
        padding: '2rem',
        borderRadius: '8px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        textAlign: 'center',
        maxWidth: '400px'
      }}>
        <h1 style={{ margin: '0 0 1rem 0', fontSize: '2rem' }}>✅ Navigation Works!</h1>
        <p style={{ margin: '0 0 1rem 0', color: '#16a34a' }}>You successfully reached the test page.</p>
        <p style={{ margin: '0 0 1rem 0', fontSize: '0.875rem' }}>
          This proves that navigation is working.
        </p>
        <TestButton />
      </div>
    </div>
  );
}

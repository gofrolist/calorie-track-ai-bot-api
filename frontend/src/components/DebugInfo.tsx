import React, { useState, useEffect } from 'react';

interface DebugInfo {
  timestamp: string;
  telegramAvailable: boolean;
  userId: string | null;
  url: string;
  hasStoredUser: boolean;
}

const DebugInfo: React.FC = () => {
  const [debugInfo, setDebugInfo] = useState<DebugInfo | null>(null);
  const [isVisible, setIsVisible] = useState(false);
  const [manualUserId, setManualUserId] = useState('');

  useEffect(() => {
    // Check if debug logging is enabled
    const enableDebugLogging = import.meta.env.VITE_ENABLE_DEBUG_LOGGING === 'true';

    if (!enableDebugLogging) {
      return;
    }

    // Poll for debug info updates
    const interval = setInterval(() => {
      const stored = localStorage.getItem('api_debug_info');
      if (stored) {
        try {
          const info = JSON.parse(stored);
          setDebugInfo(info);
        } catch {
          // Ignore parsing errors
        }
      }
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const handleManualUserIdSubmit = () => {
    if (manualUserId.trim()) {
      localStorage.setItem('telegram_user', JSON.stringify({ id: manualUserId }));
      // Trigger a page reload to pick up the new user ID
      window.location.reload();
    }
  };

  // Only show if debug logging is enabled
  const enableDebugLogging = import.meta.env.VITE_ENABLE_DEBUG_LOGGING === 'true';
  if (!enableDebugLogging) {
    return null;
  }

  return (
    <div style={{
      position: 'fixed',
      top: '10px',
      right: '10px',
      background: 'rgba(0, 0, 0, 0.8)',
      color: 'white',
      padding: '10px',
      borderRadius: '5px',
      fontSize: '12px',
      zIndex: 9999,
      maxWidth: '300px',
      cursor: 'pointer'
    }} onClick={() => setIsVisible(!isVisible)}>
      <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>
        🔍 Debug Info {isVisible ? '▼' : '▶'}
      </div>

      {isVisible && debugInfo && (
        <div style={{ lineHeight: '1.4' }}>
          <div><strong>Telegram:</strong> {debugInfo.telegramAvailable ? '✅' : '❌'}</div>
          <div><strong>User ID:</strong> {debugInfo.userId || '❌ Not found'}</div>
          <div><strong>Stored User:</strong> {debugInfo.hasStoredUser ? '✅' : '❌'}</div>
          <div><strong>Last API:</strong> {debugInfo.url}</div>
          <div><strong>Time:</strong> {new Date(debugInfo.timestamp).toLocaleTimeString()}</div>

          <div style={{ marginTop: '10px', fontSize: '10px', opacity: 0.7 }}>
            <div>Environment: {import.meta.env.VITE_APP_ENV}</div>
            <div>API Base: {import.meta.env.VITE_API_BASE_URL}</div>
          </div>

          {/* Manual User ID Input */}
          <div style={{ marginTop: '10px', padding: '5px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px' }}>
            <div style={{ fontSize: '10px', marginBottom: '3px' }}>Manual User ID:</div>
            <input
              type="text"
              value={manualUserId}
              onChange={(e) => setManualUserId(e.target.value)}
              placeholder="Enter user ID"
              style={{
                width: '100%',
                padding: '2px',
                fontSize: '10px',
                background: 'white',
                color: 'black',
                border: 'none',
                borderRadius: '2px'
              }}
            />
            <button
              onClick={handleManualUserIdSubmit}
              style={{
                marginTop: '3px',
                padding: '2px 5px',
                fontSize: '10px',
                background: '#007aff',
                color: 'white',
                border: 'none',
                borderRadius: '2px',
                cursor: 'pointer'
              }}
            >
              Set User ID
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DebugInfo;

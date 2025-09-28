import React from 'react';
import { api } from './api';

export type ConnectionStatus = 'connected' | 'disconnected' | 'error' | 'checking';

export interface ConnectivityState {
  status: ConnectionStatus;
  lastCheck: Date | null;
  responseTimeMs: number | null;
  errorMessage: string | null;
  retryCount: number;
  isMonitoring: boolean;
}

export interface ConnectivityEvent {
  status: ConnectionStatus;
  responseTimeMs?: number;
  errorMessage?: string;
  timestamp: number;
}

export interface ConnectivityResponse {
  status: 'connected' | 'disconnected' | 'error';
  response_time_ms: number;
  timestamp: string;
  correlation_id: string;
  details?: any;
}

// Connectivity monitoring service class
export class ConnectivityService {
  private static instance: ConnectivityService;
  private currentState: ConnectivityState;
  private listeners: Set<(event: ConnectivityEvent) => void> = new Set();
  private monitoringInterval?: NodeJS.Timeout;
  private retryTimeout?: NodeJS.Timeout;
  private abortController?: AbortController;

  // Configuration
  private readonly CHECK_INTERVAL = 30000; // 30 seconds
  private readonly RETRY_DELAYS = [1000, 2000, 5000, 10000, 20000]; // Exponential backoff
  private readonly MAX_RETRIES = 5;
  private readonly REQUEST_TIMEOUT = 10000; // 10 seconds

  private constructor() {
    this.currentState = {
      status: 'disconnected',
      lastCheck: null,
      responseTimeMs: null,
      errorMessage: null,
      retryCount: 0,
      isMonitoring: false
    };
  }

  public static getInstance(): ConnectivityService {
    if (!ConnectivityService.instance) {
      ConnectivityService.instance = new ConnectivityService();
    }
    return ConnectivityService.instance;
  }

  /**
   * Get current connectivity state
   */
  getState(): ConnectivityState {
    return { ...this.currentState };
  }

  /**
   * Start monitoring connectivity
   */
  startMonitoring(): void {
    if (this.currentState.isMonitoring) return;

    this.updateState({ isMonitoring: true });

    // Perform initial check
    this.checkConnectivity();

    // Set up periodic checks
    this.monitoringInterval = setInterval(() => {
      this.checkConnectivity();
    }, this.CHECK_INTERVAL);

    console.log('Connectivity monitoring started');
  }

  /**
   * Stop monitoring connectivity
   */
  stopMonitoring(): void {
    if (!this.currentState.isMonitoring) return;

    this.updateState({ isMonitoring: false });

    // Clear intervals and timeouts
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = undefined;
    }

    if (this.retryTimeout) {
      clearTimeout(this.retryTimeout);
      this.retryTimeout = undefined;
    }

    // Cancel ongoing request
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = undefined;
    }

    console.log('Connectivity monitoring stopped');
  }

  /**
   * Perform immediate connectivity check
   */
  async checkConnectivity(): Promise<ConnectivityState> {
    if (this.currentState.status === 'checking') {
      return this.currentState; // Already checking
    }

    this.updateState({
      status: 'checking',
      lastCheck: new Date()
    });

    // Cancel previous request if still pending
    if (this.abortController) {
      this.abortController.abort();
    }

    this.abortController = new AbortController();

    try {
      const startTime = performance.now();

      const response = await api.get('/health/connectivity', {
        timeout: this.REQUEST_TIMEOUT,
        signal: this.abortController.signal,
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache',
          'X-Connectivity-Check': 'true'
        }
      });

      const endTime = performance.now();
      const responseTimeMs = Math.round(endTime - startTime);

      const data = response.data as ConnectivityResponse;

      // Update state based on response
      const newStatus: ConnectionStatus = data.status === 'connected' ? 'connected' : 'error';

      this.updateState({
        status: newStatus,
        responseTimeMs,
        errorMessage: null,
        retryCount: 0
      });

      // Notify listeners
      this.notifyListeners({
        status: newStatus,
        responseTimeMs,
        timestamp: Date.now()
      });

      return this.currentState;

    } catch (error: any) {
      let errorMessage = 'Connection failed';
      let status: ConnectionStatus = 'disconnected';

      if (error.name === 'AbortError') {
        // Request was cancelled
        return this.currentState;
      }

      if (error.response) {
        // Server responded with error status
        status = 'error';
        errorMessage = `Server error: ${error.response.status}`;
      } else if (error.request) {
        // Network error
        status = 'disconnected';
        errorMessage = 'Network error';
      } else {
        // Other error
        status = 'error';
        errorMessage = error.message || 'Unknown error';
      }

      this.updateState({
        status,
        responseTimeMs: null,
        errorMessage,
        retryCount: this.currentState.retryCount + 1
      });

      // Notify listeners
      this.notifyListeners({
        status,
        errorMessage,
        timestamp: Date.now()
      });

      // Schedule retry if monitoring is enabled and within retry limits
      if (this.currentState.isMonitoring && this.currentState.retryCount <= this.MAX_RETRIES) {
        this.scheduleRetry();
      }

      return this.currentState;
    }
  }

  /**
   * Add connectivity change listener
   */
  addListener(listener: (event: ConnectivityEvent) => void): () => void {
    this.listeners.add(listener);

    // Return unsubscribe function
    return () => {
      this.listeners.delete(listener);
    };
  }

  /**
   * Remove all listeners
   */
  removeAllListeners(): void {
    this.listeners.clear();
  }

  /**
   * Reset retry count
   */
  resetRetryCount(): void {
    this.updateState({ retryCount: 0 });
  }

  /**
   * Check if network is available (browser API)
   */
  isNetworkAvailable(): boolean {
    if (typeof navigator !== 'undefined' && 'onLine' in navigator) {
      return navigator.onLine;
    }
    return true; // Assume available if can't detect
  }

  /**
   * Get connection quality estimate
   */
  getConnectionQuality(): 'excellent' | 'good' | 'poor' | 'unknown' {
    const responseTime = this.currentState.responseTimeMs;

    if (responseTime === null || this.currentState.status !== 'connected') {
      return 'unknown';
    }

    if (responseTime < 100) return 'excellent';
    if (responseTime < 300) return 'good';
    return 'poor';
  }

  /**
   * Dispose service and cleanup
   */
  dispose(): void {
    this.stopMonitoring();
    this.removeAllListeners();
  }

  // Private methods

  /**
   * Update internal state
   */
  private updateState(updates: Partial<ConnectivityState>): void {
    this.currentState = {
      ...this.currentState,
      ...updates
    };
  }

  /**
   * Schedule retry with exponential backoff
   */
  private scheduleRetry(): void {
    if (this.retryTimeout) {
      clearTimeout(this.retryTimeout);
    }

    const retryIndex = Math.min(this.currentState.retryCount - 1, this.RETRY_DELAYS.length - 1);
    const delay = this.RETRY_DELAYS[retryIndex];

    console.log(`Scheduling connectivity retry #${this.currentState.retryCount} in ${delay}ms`);

    this.retryTimeout = setTimeout(() => {
      this.checkConnectivity();
    }, delay);
  }

  /**
   * Notify all listeners of connectivity change
   */
  private notifyListeners(event: ConnectivityEvent): void {
    this.listeners.forEach(listener => {
      try {
        listener(event);
      } catch (error) {
        console.error('Error in connectivity change listener:', error);
      }
    });
  }
}

// Export singleton instance
export const connectivityService = ConnectivityService.getInstance();

// React hook for connectivity monitoring
export const useConnectivity = (options: { autoStart?: boolean } = {}) => {
  const { autoStart = true } = options;
  const [connectivityState, setConnectivityState] = React.useState<ConnectivityState>(
    connectivityService.getState()
  );

  React.useEffect(() => {
    // Subscribe to connectivity changes
    const unsubscribe = connectivityService.addListener((event) => {
      setConnectivityState(connectivityService.getState());
    });

    // Update state immediately
    setConnectivityState(connectivityService.getState());

    // Auto-start monitoring if requested
    if (autoStart && !connectivityService.getState().isMonitoring) {
      connectivityService.startMonitoring();
    }

    return () => {
      unsubscribe();
      // Don't stop monitoring on unmount - other components might be using it
    };
  }, [autoStart]);

  // Listen for browser online/offline events
  React.useEffect(() => {
    const handleOnline = () => {
      console.log('Browser reported online status');
      if (connectivityService.getState().isMonitoring) {
        connectivityService.checkConnectivity();
      }
    };

    const handleOffline = () => {
      console.log('Browser reported offline status');
      // Update state to reflect offline status
      connectivityService['updateState']({
        status: 'disconnected',
        errorMessage: 'Browser offline'
      });
    };

    if (typeof window !== 'undefined') {
      window.addEventListener('online', handleOnline);
      window.addEventListener('offline', handleOffline);

      return () => {
        window.removeEventListener('online', handleOnline);
        window.removeEventListener('offline', handleOffline);
      };
    }
  }, []);

  return {
    ...connectivityState,
    checkConnectivity: () => connectivityService.checkConnectivity(),
    startMonitoring: () => connectivityService.startMonitoring(),
    stopMonitoring: () => connectivityService.stopMonitoring(),
    resetRetryCount: () => connectivityService.resetRetryCount(),
    isNetworkAvailable: connectivityService.isNetworkAvailable(),
    connectionQuality: connectivityService.getConnectionQuality()
  };
};

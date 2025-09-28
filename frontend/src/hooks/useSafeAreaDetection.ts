/**
 * Custom hooks for safe area detection and management
 *
 * Provides React hooks that encapsulate safe area detection logic,
 * event handling, and state management with proper cleanup and optimization.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  SafeAreaValues,
  calculateSafeAreaValues,
  createDebouncedSafeAreaDetection,
  detectSafeAreaSupport,
  deviceLikelyHasSafeAreas,
  getFallbackSafeAreaValues,
  testCssEnvSupport,
  validateSafeAreaValues
} from '../utils/safe-area-detection';

export interface UseSafeAreaOptions {
  /**
   * Enable automatic detection of safe area changes
   * @default true
   */
  enableAutoDetection?: boolean;

  /**
   * Debounce delay for resize/orientation change events (ms)
   * @default 100
   */
  debounceDelay?: number;

  /**
   * Enable debug logging
   * @default false
   */
  debugMode?: boolean;

  /**
   * Force recalculation even if device unlikely to have safe areas
   * @default false
   */
  forceCalculation?: boolean;
}

export interface SafeAreaDetectionResult {
  /** Current safe area values */
  values: SafeAreaValues;

  /** Whether CSS env() is supported by the browser */
  isSupported: boolean;

  /** Whether the device is likely running in Telegram WebApp */
  isInTelegram: boolean;

  /** Whether detection is currently in progress */
  isDetecting: boolean;

  /** Whether device likely has safe areas */
  deviceHasSafeAreas: boolean;

  /** Manually trigger safe area detection */
  detect: () => Promise<void>;

  /** Force refresh of safe area values */
  refresh: () => Promise<void>;
}

/**
 * Hook for detecting and managing safe area values
 *
 * Provides comprehensive safe area detection with automatic updates
 * on orientation changes, proper cleanup, and performance optimization.
 *
 * @param options Configuration options for detection behavior
 * @returns SafeAreaDetectionResult with current values and control functions
 */
export const useSafeAreaDetection = (options: UseSafeAreaOptions = {}): SafeAreaDetectionResult => {
  const {
    enableAutoDetection = true,
    debounceDelay = 100,
    debugMode = false,
    forceCalculation = false
  } = options;

  // State management
  const [values, setValues] = useState<SafeAreaValues>({ top: 0, bottom: 0, left: 0, right: 0 });
  const [isSupported, setIsSupported] = useState<boolean>(false);
  const [isDetecting, setIsDetecting] = useState<boolean>(false);
  const [deviceHasSafeAreas, setDeviceHasSafeAreas] = useState<boolean>(false);

  // Refs for cleanup and optimization
  const debouncedDetectRef = useRef<(() => void) | null>(null);
  const mountedRef = useRef<boolean>(true);
  const lastDetectionRef = useRef<number>(0);

  // Check if running in Telegram WebApp
  const isInTelegram = typeof window !== 'undefined' && !!(window as any).Telegram?.WebApp;

  /**
   * Core detection function with comprehensive error handling and optimization
   */
  const detectSafeAreas = useCallback(async (): Promise<void> => {
    if (!mountedRef.current) return;

    // Prevent rapid successive detections
    const now = Date.now();
    if (now - lastDetectionRef.current < 50) {
      if (debugMode) {
        console.log('useSafeAreaDetection: Skipping detection (too rapid)');
      }
      return;
    }
    lastDetectionRef.current = now;

    setIsDetecting(true);

    try {
      // Check device characteristics
      const deviceLikely = deviceLikelyHasSafeAreas();
      setDeviceHasSafeAreas(deviceLikely);

      if (!deviceLikely && !forceCalculation) {
        if (debugMode) {
          console.log('useSafeAreaDetection: Device unlikely to have safe areas, skipping');
        }
        setValues({ top: 0, bottom: 0, left: 0, right: 0 });
        setIsSupported(false);
        setIsDetecting(false);
        return;
      }

      // Test CSS env() support
      const envSupported = testCssEnvSupport();
      setIsSupported(envSupported);

      let detectedValues: SafeAreaValues;

      if (envSupported) {
        // Use CSS env() functions for accurate detection
        detectedValues = await calculateSafeAreaValues();

        if (debugMode) {
          console.log('useSafeAreaDetection: CSS env() detection completed', detectedValues);
        }
      } else {
        // Use fallback detection
        detectedValues = getFallbackSafeAreaValues();

        if (debugMode) {
          console.log('useSafeAreaDetection: Fallback detection used', detectedValues);
        }
      }

      // Validate and set values
      const validatedValues = validateSafeAreaValues(detectedValues);

      if (mountedRef.current) {
        setValues(validatedValues);

        if (debugMode) {
          console.log('useSafeAreaDetection: Final values set', {
            original: detectedValues,
            validated: validatedValues,
            supported: envSupported,
            telegram: isInTelegram
          });
        }
      }
    } catch (error) {
      console.warn('useSafeAreaDetection: Error during detection:', error);

      if (mountedRef.current) {
        // Set fallback values on error
        const fallbackValues = getFallbackSafeAreaValues();
        setValues(validateSafeAreaValues(fallbackValues));
        setIsSupported(false);
      }
    } finally {
      if (mountedRef.current) {
        setIsDetecting(false);
      }
    }
  }, [debugMode, forceCalculation, isInTelegram]);

  /**
   * Refresh function for manual triggering
   */
  const refresh = useCallback(async (): Promise<void> => {
    lastDetectionRef.current = 0; // Reset throttling
    await detectSafeAreas();
  }, [detectSafeAreas]);

  /**
   * Setup effect for initial detection and event listeners
   */
  useEffect(() => {
    if (!enableAutoDetection) return;

    // Initial detection
    detectSafeAreas();

    // Create debounced detection function
    const debouncedDetect = createDebouncedSafeAreaDetection(
      (newValues) => {
        if (mountedRef.current) {
          setValues(newValues);
        }
      },
      debounceDelay
    );

    debouncedDetectRef.current = debouncedDetect;

    // Event handlers with comprehensive device support
    const handleResize = () => {
      if (debugMode) {
        console.log('useSafeAreaDetection: Resize event triggered');
      }
      debouncedDetect();
    };

    const handleOrientationChange = () => {
      if (debugMode) {
        console.log('useSafeAreaDetection: Orientation change triggered');
      }
      // Longer delay for orientation changes to allow layout settlement
      setTimeout(debouncedDetect, 150);
    };

    const handleVisualViewportChange = () => {
      if (debugMode) {
        console.log('useSafeAreaDetection: Visual viewport change triggered');
      }
      debouncedDetect();
    };

    // Add event listeners with feature detection
    window.addEventListener('resize', handleResize, { passive: true });
    window.addEventListener('orientationchange', handleOrientationChange, { passive: true });

    // Modern visual viewport API for better mobile support
    if ((window as any).visualViewport) {
      (window as any).visualViewport.addEventListener('resize', handleVisualViewportChange, { passive: true });
    }

    // Screen orientation API for additional orientation detection
    if ((window as any).screen?.orientation) {
      (window as any).screen.orientation.addEventListener('change', handleOrientationChange, { passive: true });
    }

    // Cleanup function
    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', handleOrientationChange);

      if ((window as any).visualViewport) {
        (window as any).visualViewport.removeEventListener('resize', handleVisualViewportChange);
      }

      if ((window as any).screen?.orientation) {
        (window as any).screen.orientation.removeEventListener('change', handleOrientationChange);
      }
    };
  }, [enableAutoDetection, debounceDelay, debugMode, detectSafeAreas]);

  /**
   * Cleanup effect
   */
  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  return {
    values,
    isSupported,
    isInTelegram,
    isDetecting,
    deviceHasSafeAreas,
    detect: detectSafeAreas,
    refresh
  };
};

/**
 * Simplified hook for basic safe area values
 *
 * Provides just the safe area values without advanced features.
 * Suitable for components that only need the current values.
 *
 * @returns SafeAreaValues with current safe area measurements
 */
export const useSafeAreaValues = (): SafeAreaValues => {
  const { values } = useSafeAreaDetection({
    enableAutoDetection: true,
    debugMode: false
  });

  return values;
};

/**
 * Hook for safe area CSS custom properties
 *
 * Automatically applies safe area values as CSS custom properties
 * to the document root for use throughout the application.
 *
 * @param enabled Whether to enable CSS custom property updates
 * @param prefix Prefix for CSS custom property names
 */
export const useSafeAreaCSSProperties = (
  enabled: boolean = true,
  prefix: string = '--safe-area'
): void => {
  const { values, isSupported } = useSafeAreaDetection({
    enableAutoDetection: enabled
  });

  useEffect(() => {
    if (!enabled || typeof document === 'undefined') return;

    const root = document.documentElement;

    // Set CSS custom properties
    root.style.setProperty(`${prefix}-top`, `${values.top}px`);
    root.style.setProperty(`${prefix}-bottom`, `${values.bottom}px`);
    root.style.setProperty(`${prefix}-left`, `${values.left}px`);
    root.style.setProperty(`${prefix}-right`, `${values.right}px`);
    root.style.setProperty(`${prefix}-supported`, isSupported ? '1' : '0');

    // Cleanup function
    return () => {
      root.style.removeProperty(`${prefix}-top`);
      root.style.removeProperty(`${prefix}-bottom`);
      root.style.removeProperty(`${prefix}-left`);
      root.style.removeProperty(`${prefix}-right`);
      root.style.removeProperty(`${prefix}-supported`);
    };
  }, [values, isSupported, enabled, prefix]);
};

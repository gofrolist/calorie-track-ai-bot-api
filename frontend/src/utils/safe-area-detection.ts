/**
 * Safe Area Detection Utilities
 *
 * Modularized utilities for detecting and managing device safe areas.
 * Provides comprehensive browser support detection, value calculation,
 * and cross-platform compatibility.
 */

export interface SafeAreaValues {
  top: number;
  bottom: number;
  left: number;
  right: number;
}

export interface SafeAreaSupport {
  cssEnvSupported: boolean;
  visualViewportSupported: boolean;
  screenOrientationSupported: boolean;
}

/**
 * Detects browser support for various safe area APIs
 *
 * @returns SafeAreaSupport object with capability flags
 */
export const detectSafeAreaSupport = (): SafeAreaSupport => {
  if (typeof window === 'undefined') {
    return {
      cssEnvSupported: false,
      visualViewportSupported: false,
      screenOrientationSupported: false
    };
  }

  const cssEnvSupported = CSS.supports && CSS.supports('padding-top: env(safe-area-inset-top)');
  const visualViewportSupported = 'visualViewport' in window;
  const screenOrientationSupported = 'screen' in window && 'orientation' in window.screen;

  return {
    cssEnvSupported,
    visualViewportSupported,
    screenOrientationSupported
  };
};

/**
 * Creates a temporary element to test CSS env() function support
 * More reliable than CSS.supports() which may give false positives
 *
 * @returns boolean indicating if env() is actually supported
 */
export const testCssEnvSupport = (): boolean => {
  if (typeof document === 'undefined') return false;

  try {
    const testElement = document.createElement('div');
    testElement.style.cssText = `
      position: fixed;
      top: -1000px;
      left: -1000px;
      width: 1px;
      height: 1px;
      visibility: hidden;
      pointer-events: none;
      padding-top: env(safe-area-inset-top);
    `;

    document.body.appendChild(testElement);

    const computedStyle = window.getComputedStyle(testElement);
    const paddingTop = computedStyle.paddingTop;

    document.body.removeChild(testElement);

    // If env() is supported, paddingTop should not be '0px' or empty
    return paddingTop !== '0px' && paddingTop !== '';
  } catch (error) {
    console.warn('Error testing CSS env() support:', error);
    return false;
  }
};

/**
 * Calculates actual safe area values using CSS env() functions
 * Uses a temporary element approach for accurate measurement
 *
 * @returns Promise<SafeAreaValues> with measured safe area values
 */
export const calculateSafeAreaValues = async (): Promise<SafeAreaValues> => {
  if (typeof document === 'undefined') {
    return { top: 0, bottom: 0, left: 0, right: 0 };
  }

  return new Promise((resolve) => {
    try {
      const measureElement = document.createElement('div');
      measureElement.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 1px;
        height: 1px;
        visibility: hidden;
        pointer-events: none;
        z-index: -1;
        padding-top: env(safe-area-inset-top);
        padding-bottom: env(safe-area-inset-bottom);
        padding-left: env(safe-area-inset-left);
        padding-right: env(safe-area-inset-right);
      `;

      document.body.appendChild(measureElement);

      // Use requestAnimationFrame to ensure styles are computed
      requestAnimationFrame(() => {
        try {
          const computed = window.getComputedStyle(measureElement);

          const values: SafeAreaValues = {
            top: parseFloat(computed.paddingTop) || 0,
            bottom: parseFloat(computed.paddingBottom) || 0,
            left: parseFloat(computed.paddingLeft) || 0,
            right: parseFloat(computed.paddingRight) || 0
          };

          document.body.removeChild(measureElement);
          resolve(values);
        } catch (error) {
          console.warn('Error calculating safe area values:', error);
          document.body.removeChild(measureElement);
          resolve({ top: 0, bottom: 0, left: 0, right: 0 });
        }
      });
    } catch (error) {
      console.warn('Error creating measurement element:', error);
      resolve({ top: 0, bottom: 0, left: 0, right: 0 });
    }
  });
};

/**
 * Provides fallback safe area values for devices without env() support
 * Uses device detection and viewport analysis
 *
 * @returns SafeAreaValues with estimated fallback values
 */
export const getFallbackSafeAreaValues = (): SafeAreaValues => {
  if (typeof window === 'undefined') {
    return { top: 0, bottom: 0, left: 0, right: 0 };
  }

  const userAgent = navigator.userAgent.toLowerCase();
  const isIOS = /iphone|ipad|ipod/.test(userAgent);
  const isAndroid = /android/.test(userAgent);
  const isNotch = window.screen.height > window.screen.width ? window.screen.height >= 812 : window.screen.width >= 812;

  // Basic fallback values based on device detection
  let fallbackValues: SafeAreaValues = { top: 0, bottom: 0, left: 0, right: 0 };

  if (isIOS) {
    // iOS devices with notch/dynamic island
    if (isNotch) {
      fallbackValues.top = 47; // iPhone X+ status bar with notch
      fallbackValues.bottom = 34; // Home indicator area
    } else {
      fallbackValues.top = 20; // Standard iOS status bar
      fallbackValues.bottom = 0;
    }
  } else if (isAndroid) {
    // Android devices - status bar is typically 24dp
    fallbackValues.top = 24;
    fallbackValues.bottom = 0;
  } else {
    // Desktop or other devices
    fallbackValues.top = 0;
    fallbackValues.bottom = 0;
  }

  return fallbackValues;
};

/**
 * Validates safe area values for reasonable bounds
 * Prevents extreme values that might break layout
 *
 * @param values SafeAreaValues to validate
 * @returns SafeAreaValues with validated/clamped values
 */
export const validateSafeAreaValues = (values: SafeAreaValues): SafeAreaValues => {
  const MAX_SAFE_AREA = 200; // Maximum reasonable safe area in pixels
  const MIN_SAFE_AREA = 0;   // Minimum safe area

  return {
    top: Math.max(MIN_SAFE_AREA, Math.min(MAX_SAFE_AREA, values.top)),
    bottom: Math.max(MIN_SAFE_AREA, Math.min(MAX_SAFE_AREA, values.bottom)),
    left: Math.max(MIN_SAFE_AREA, Math.min(MAX_SAFE_AREA, values.left)),
    right: Math.max(MIN_SAFE_AREA, Math.min(MAX_SAFE_AREA, values.right))
  };
};

/**
 * Combines safe area values with priority order
 * Useful for merging detected values with fallbacks
 *
 * @param primary Primary safe area values (highest priority)
 * @param fallback Fallback safe area values (used when primary is 0)
 * @returns SafeAreaValues with combined values
 */
export const combineSafeAreaValues = (
  primary: SafeAreaValues,
  fallback: SafeAreaValues
): SafeAreaValues => {
  return {
    top: primary.top > 0 ? primary.top : fallback.top,
    bottom: primary.bottom > 0 ? primary.bottom : fallback.bottom,
    left: primary.left > 0 ? primary.left : fallback.left,
    right: primary.right > 0 ? primary.right : fallback.right
  };
};

/**
 * Debounced safe area detection function
 * Prevents excessive recalculation during rapid resize events
 *
 * @param callback Function to call with new safe area values
 * @param delay Debounce delay in milliseconds
 * @returns Debounced function
 */
export const createDebouncedSafeAreaDetection = (
  callback: (values: SafeAreaValues) => void,
  delay: number = 100
): (() => void) => {
  let timeoutId: NodeJS.Timeout | null = null;

  return () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    timeoutId = setTimeout(async () => {
      try {
        const support = detectSafeAreaSupport();
        let values: SafeAreaValues;

        if (support.cssEnvSupported) {
          values = await calculateSafeAreaValues();
        } else {
          values = getFallbackSafeAreaValues();
        }

        const validatedValues = validateSafeAreaValues(values);
        callback(validatedValues);
      } catch (error) {
        console.warn('Error in debounced safe area detection:', error);
        callback({ top: 0, bottom: 0, left: 0, right: 0 });
      }
    }, delay);
  };
};

/**
 * Checks if device likely has safe areas that need handling
 * Used for optimization - avoid unnecessary calculations on desktop
 *
 * @returns boolean indicating if safe area handling is likely needed
 */
export const deviceLikelyHasSafeAreas = (): boolean => {
  if (typeof window === 'undefined') return false;

  const userAgent = navigator.userAgent.toLowerCase();
  const isIOS = /iphone|ipad|ipod/.test(userAgent);
  const isAndroid = /android/.test(userAgent);
  const isMobile = /mobile|tablet/.test(userAgent);

  // Check for high aspect ratio screens (likely to have notches/safe areas)
  const aspectRatio = window.screen.height / window.screen.width;
  const hasHighAspectRatio = aspectRatio > 2 || aspectRatio < 0.5;

  return (isIOS || isAndroid || isMobile) && hasHighAspectRatio;
};

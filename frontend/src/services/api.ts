import axios, { AxiosResponse } from 'axios';
import { v4 as uuidv4 } from 'uuid';

// Types based on data-model.md
export interface User {
  id: string;
  telegram_user_id: number;
  language: 'en' | 'ru';
  created_at: string;
  updated_at: string;
}

export interface FoodPhoto {
  id: string;
  user_id: string;
  object_key: string;
  content_type: string;
  created_at: string;
}

export interface Estimate {
  id: string;
  photo_id: string;
  kcal_mean: number;
  kcal_min: number;
  kcal_max: number;
  confidence: number;
  breakdown: Array<{
    label: string;
    kcal: number;
    confidence: number;
  }>;
  status: 'queued' | 'running' | 'done' | 'failed';
  created_at: string;
  updated_at: string;
}

export interface Meal {
  id: string;
  userId: string;
  createdAt: string;
  description: string | null;
  calories: number;
  macronutrients: {
    protein: number;
    carbs: number;
    fats: number;
  };
  photos: Array<{
    id: string;
    thumbnailUrl: string;
    fullUrl: string;
    displayOrder: number;
  }>;
  confidenceScore: number | null;
}

export interface DailySummary {
  user_id: string;
  date: string;
  kcal_total: number;
  macros_totals?: {
    protein_g?: number;
    fat_g?: number;
    carbs_g?: number;
  };
}

export interface InlineAnalyticsFailureReason {
  reason: string;
  count: number;
}

export interface InlineAnalyticsBucket {
  date: string;
  chat_type: 'private' | 'group';
  request_count: number;
  success_count: number;
  failure_count: number;
  permission_block_count: number;
  avg_ack_latency_ms: number;
  p95_result_latency_ms: number;
  accuracy_within_tolerance_pct: number;
  trigger_counts: Record<string, number>;
  failure_reasons: InlineAnalyticsFailureReason[];
}

export interface InlineAnalyticsSummary {
  range: {
    start: string;
    end: string;
  };
  buckets: InlineAnalyticsBucket[];
  sla: {
    ack_target_ms: number;
    result_target_ms: number;
  };
  accuracy: {
    tolerance_pct: number;
    benchmark_dataset: string;
  };
}

export interface Goal {
  user_id: string;
  daily_kcal_target: number;
  created_at: string;
  updated_at: string;
}

// UI Configuration types
export interface UIConfiguration {
  id: string;
  environment: 'development' | 'production';
  api_base_url: string;
  safe_area_top: number;
  safe_area_bottom: number;
  safe_area_left: number;
  safe_area_right: number;
  theme: 'light' | 'dark' | 'auto';
  theme_source: 'telegram' | 'system' | 'manual';
  language: string;
  language_source: 'telegram' | 'browser' | 'manual';
  features: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface UIConfigurationUpdate {
  environment?: 'development' | 'production';
  api_base_url?: string;
  safe_area_top?: number;
  safe_area_bottom?: number;
  safe_area_left?: number;
  safe_area_right?: number;
  theme?: 'light' | 'dark' | 'auto';
  theme_source?: 'telegram' | 'system' | 'manual';
  language?: string;
  language_source?: 'telegram' | 'browser' | 'manual';
  features?: Record<string, any>;
}

export interface ThemeDetectionResponse {
  theme: 'light' | 'dark' | 'auto';
  theme_source: 'telegram' | 'system' | 'manual';
  telegram_color_scheme?: 'light' | 'dark';
  system_prefers_dark?: boolean;
  detected_at: string;
}

export interface LanguageDetectionResponse {
  language: string;
  language_source: 'telegram' | 'browser' | 'manual';
  telegram_language?: string;
  browser_language?: string;
  supported_languages: string[];
  detected_at: string;
}

export interface ConnectivityResponse {
  status: 'connected' | 'disconnected' | 'error';
  response_time_ms: number;
  timestamp: string;
  correlation_id: string;
  details?: Record<string, any>;
}

export interface LogEntry {
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  service: string;
  correlation_id: string;
  message: string;
  context?: Record<string, any>;
  user_id?: string;
  timestamp: string;
}

import { config } from '../config';

// API Configuration using centralized config
const API_BASE_URL = config.apiBaseUrl;

// Session management
class SessionManager {
  private sessionToken: string | null = null;
  private correlationId: string | null = null;

  setSession(token: string) {
    this.sessionToken = token;
    localStorage.setItem('session_token', token);
  }

  getSession(): string | null {
    if (!this.sessionToken) {
      this.sessionToken = localStorage.getItem('session_token');
    }
    return this.sessionToken;
  }

  clearSession() {
    this.sessionToken = null;
    localStorage.removeItem('session_token');
  }

  generateCorrelationId(): string {
    this.correlationId = uuidv4();
    return this.correlationId;
  }

  getCorrelationId(): string {
    return this.correlationId || this.generateCorrelationId();
  }
}

const sessionManager = new SessionManager();

// Axios instance
export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: config.apiTimeout,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use((config) => {
  // Add correlation ID for observability
  config.headers['X-Correlation-ID'] = sessionManager.getCorrelationId();

  // Add session token if available
  const sessionToken = sessionManager.getSession();
  if (sessionToken) {
    config.headers.Authorization = `Bearer ${sessionToken}`;
  }

  // Add Telegram user ID for backend authentication in development
  let userId = null;

  // Try to get user ID from Telegram WebApp
  if (window.Telegram?.WebApp?.initDataUnsafe?.user?.id) {
    userId = window.Telegram.WebApp.initDataUnsafe.user.id.toString();
  }

  // Fallback: try to get from URL parameters or other sources
  if (!userId) {
    // Check if we're in a Telegram WebApp environment
    const urlParams = new URLSearchParams(window.location.search);
    userId = urlParams.get('user_id') ||
             urlParams.get('tg_user_id') ||
             urlParams.get('user') ||
             urlParams.get('id');

    // Also check hash parameters
    if (!userId && window.location.hash) {
      const hashParams = new URLSearchParams(window.location.hash.substring(1));
      userId = hashParams.get('user_id') ||
               hashParams.get('tg_user_id') ||
               hashParams.get('user') ||
               hashParams.get('id');
    }
  }

  // Additional fallback: check if we have stored user info
  if (!userId) {
    try {
      const storedUser = localStorage.getItem('telegram_user');
      if (storedUser) {
        const userData = JSON.parse(storedUser);
        userId = userData.id?.toString();
      }
    } catch (e) {
      // Ignore parsing errors
    }
  }

  // Debug logging - enable with VITE_ENABLE_DEBUG_LOGGING=true
  const enableDebugLogging = import.meta.env.VITE_ENABLE_DEBUG_LOGGING === 'true' ||
                            config.baseURL?.includes('localhost') ||
                            process.env.NODE_ENV === 'development';

  if (enableDebugLogging) {
    console.log('API Request Debug:', {
      telegramAvailable: !!window.Telegram?.WebApp,
      userId,
      initDataUnsafe: window.Telegram?.WebApp?.initDataUnsafe,
      url: config.url,
      storedUser: localStorage.getItem('telegram_user'),
      headers: config.headers
    });

    // Store debug info in localStorage for UI display
    const debugInfo = {
      timestamp: new Date().toISOString(),
      telegramAvailable: !!window.Telegram?.WebApp,
      userId,
      url: config.url,
      hasStoredUser: !!localStorage.getItem('telegram_user')
    };
    localStorage.setItem('api_debug_info', JSON.stringify(debugInfo));
  }

  if (userId) {
    config.headers['x-user-id'] = userId;
  }

  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear invalid session
      sessionManager.clearSession();
    }

    // Log errors in development
    if (config.features.enableDebugLogging) {
      console.error('API Error:', {
        url: error.config?.url,
        method: error.config?.method,
        status: error.response?.status,
        data: error.response?.data,
      });
    }

    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  async initTelegramAuth(initData: string): Promise<{ session_token: string; user: User }> {
    const response = await api.post('/api/v1/auth/telegram/init', {
      init_data: initData,
    });

    // Store session token
    sessionManager.setSession(response.data.session_token);

    return response.data;
  },
};

// Photos API
export const photosApi = {
  async createPhoto(contentType: string): Promise<{ photo: FoodPhoto; upload_url: string }> {
    const response = await api.post('/api/v1/photos', {
      content_type: contentType,
    });
    return response.data;
  },

  async uploadToPresignedUrl(uploadUrl: string, file: File): Promise<void> {
    await axios.put(uploadUrl, file, {
      headers: {
        'Content-Type': file.type,
      },
    });
  },

  async requestEstimate(photoId: string): Promise<{ estimate_id: string }> {
    const response = await api.post(`/api/v1/photos/${photoId}/estimate`);
    return response.data;
  },
};

// Estimates API
export const estimatesApi = {
  async getEstimate(estimateId: string): Promise<Estimate> {
    const response = await api.get(`/api/v1/estimates/${estimateId}`);
    return response.data;
  },
};

// Meals API
export const mealsApi = {
  async createMeal(mealData: Partial<Meal>): Promise<Meal> {
    const response = await api.post('/api/v1/meals', mealData);
    return response.data;
  },

  async getMeal(mealId: string): Promise<Meal> {
    const response = await api.get(`/api/v1/meals/${mealId}`);
    return response.data;
  },

  async updateMeal(mealId: string, mealData: Partial<Meal>): Promise<Meal> {
    const response = await api.patch(`/api/v1/meals/${mealId}`, mealData);
    return response.data;
  },

  async deleteMeal(mealId: string): Promise<void> {
    await api.delete(`/api/v1/meals/${mealId}`);
  },

  async getMealsByDate(date: string): Promise<{ meals: Meal[]; total: number }> {
    const response = await api.get('/api/v1/meals', {
      params: { date },
    });

    // Transform snake_case to camelCase for frontend components
    const transformedMeals = response.data.meals.map((meal: any) => ({
      id: meal.id,
      userId: meal.user_id,
      createdAt: meal.created_at,
      description: meal.description,
      calories: meal.calories,
      macronutrients: meal.macronutrients,
      photos: meal.photos?.map((photo: any) => ({
        id: photo.id,
        thumbnailUrl: photo.thumbnail_url,
        fullUrl: photo.full_url,
        displayOrder: photo.display_order,
      })) || [],
      confidenceScore: meal.confidence_score,
    }));

    return {
      meals: transformedMeals,
      total: response.data.total,
    };
  },

  async getMealsByDateRange(startDate: string, endDate: string, limit?: number): Promise<{ meals: Meal[]; total: number }> {
    const response = await api.get('/api/v1/meals', {
      params: { start_date: startDate, end_date: endDate, limit },
    });

    // Transform snake_case to camelCase for frontend components
    const transformedMeals = response.data.meals.map((meal: any) => ({
      id: meal.id,
      userId: meal.user_id,
      createdAt: meal.created_at,
      description: meal.description,
      calories: meal.calories,
      macronutrients: meal.macronutrients,
      photos: meal.photos?.map((photo: any) => ({
        id: photo.id,
        thumbnailUrl: photo.thumbnail_url,
        fullUrl: photo.full_url,
        displayOrder: photo.display_order,
      })) || [],
      confidenceScore: meal.confidence_score,
    }));

    return {
      meals: transformedMeals,
      total: response.data.total,
    };
  },

  async getMealsCalendar(startDate: string, endDate: string): Promise<{
    dates: Array<{
      meal_date: string;
      meal_count: number;
      total_calories: number;
      total_protein: number;
      total_carbs: number;
      total_fats: number;
    }>;
  }> {
    const response = await api.get('/api/v1/meals/calendar', {
      params: { start_date: startDate, end_date: endDate },
    });
    return response.data;
  },
};

// Daily Summary API
export const dailySummaryApi = {
  async getDailySummary(date: string): Promise<DailySummary> {
    const response = await api.get(`/api/v1/daily-summary/${date}`);
    return response.data;
  },

  async getTodayData(date: string): Promise<{ meals: Meal[]; daily_summary: DailySummary }> {
    const response = await api.get(`/api/v1/today/${date}`);
    return response.data;
  },

  async getWeeklySummary(startDate: string): Promise<DailySummary[]> {
    const response = await api.get('/api/v1/weekly-summary', {
      params: { start_date: startDate },
    });
    return response.data;
  },

  async getMonthlySummary(year: number, month: number): Promise<DailySummary[]> {
    const response = await api.get('/api/v1/monthly-summary', {
      params: { year, month },
    });
    return response.data;
  },
};

// Goals API
export const goalsApi = {
  async getGoal(): Promise<Goal | null> {
    try {
      const response = await api.get('/api/v1/goals');
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  async createGoal(dailyKcalTarget: number): Promise<Goal> {
    const response = await api.post('/api/v1/goals', {
      daily_kcal_target: dailyKcalTarget,
    });
    return response.data;
  },

  async updateGoal(dailyKcalTarget: number): Promise<Goal> {
    const response = await api.patch('/api/v1/goals', {
      daily_kcal_target: dailyKcalTarget,
    });
    return response.data;
  },
};

export const analyticsApi = {
  async getInlineSummary(params?: {
    rangeStart?: string;
    rangeEnd?: string;
    chatType?: 'private' | 'group';
  }): Promise<InlineAnalyticsSummary> {
    const response = await api.get('/api/v1/analytics/inline-summary', {
      params: {
        range_start: params?.rangeStart,
        range_end: params?.rangeEnd,
        chat_type: params?.chatType,
      },
    });

    return response.data;
  },
};

// Health API
export const healthApi = {
  async checkHealth(): Promise<{ status: string }> {
    const response = await api.get('/health/live');
    return response.data;
  },

  async checkConnectivity(): Promise<ConnectivityResponse> {
    const response = await api.get('/health/connectivity');
    return response.data;
  },
};

// Configuration API
export const configApi = {
  async getUIConfiguration(): Promise<UIConfiguration> {
    const response = await api.get('/api/v1/config/ui');
    return response.data;
  },

  async updateUIConfiguration(updates: UIConfigurationUpdate): Promise<UIConfiguration> {
    const response = await api.put('/api/v1/config/ui', updates);
    return response.data;
  },

  async patchUIConfiguration(updates: UIConfigurationUpdate): Promise<UIConfiguration> {
    const response = await api.patch('/api/v1/config/ui', updates);
    return response.data;
  },

  async detectTheme(): Promise<ThemeDetectionResponse> {
    // Add theme detection headers if available
    const headers: Record<string, string> = {};

    if (window.Telegram?.WebApp?.colorScheme) {
      headers['x-telegram-color-scheme'] = window.Telegram.WebApp.colorScheme;
    }

    // Add system preference header
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      headers['sec-ch-prefers-color-scheme'] = 'dark';
    }

    const response = await api.get('/api/v1/config/theme', { headers });
    return response.data;
  },

  async detectLanguage(): Promise<LanguageDetectionResponse> {
    // Add language detection headers if available
    const headers: Record<string, string> = {};

    if (window.Telegram?.WebApp?.initDataUnsafe?.user?.language_code) {
      headers['x-telegram-language-code'] = window.Telegram.WebApp.initDataUnsafe.user.language_code;
    }

    if (navigator.language) {
      headers['accept-language'] = navigator.language;
    }

    const response = await api.get('/api/v1/config/language', { headers });
    return response.data;
  },
};

// Logging API
export const loggingApi = {
  async submitLog(logEntry: Omit<LogEntry, 'timestamp'>): Promise<void> {
    const logWithTimestamp: LogEntry = {
      ...logEntry,
      timestamp: new Date().toISOString(),
    };

    await api.post('/api/v1/logs', logWithTimestamp);
  },

  async getLogs(params?: {
    level?: string;
    service?: string;
    correlation_id?: string;
    limit?: number;
    offset?: number;
  }): Promise<LogEntry[]> {
    const response = await api.get('/api/v1/logs', { params });
    return response.data;
  },

  // Helper methods for different log levels
  async logDebug(message: string, context?: Record<string, any>, service = 'frontend'): Promise<void> {
    await this.submitLog({
      level: 'DEBUG',
      service,
      correlation_id: sessionManager.getCorrelationId(),
      message,
      context,
    });
  },

  async logInfo(message: string, context?: Record<string, any>, service = 'frontend'): Promise<void> {
    await this.submitLog({
      level: 'INFO',
      service,
      correlation_id: sessionManager.getCorrelationId(),
      message,
      context,
    });
  },

  async logWarning(message: string, context?: Record<string, any>, service = 'frontend'): Promise<void> {
    await this.submitLog({
      level: 'WARNING',
      service,
      correlation_id: sessionManager.getCorrelationId(),
      message,
      context,
    });
  },

  async logError(message: string, context?: Record<string, any>, service = 'frontend'): Promise<void> {
    await this.submitLog({
      level: 'ERROR',
      service,
      correlation_id: sessionManager.getCorrelationId(),
      message,
      context,
    });
  },

  async logCritical(message: string, context?: Record<string, any>, service = 'frontend'): Promise<void> {
    await this.submitLog({
      level: 'CRITICAL',
      service,
      correlation_id: sessionManager.getCorrelationId(),
      message,
      context,
    });
  },
};

// Development API (only available in development environment)
export const devApi = {
  async getEnvironmentInfo(): Promise<any> {
    const response = await api.get('/api/v1/dev/environment');
    return response.data;
  },

  async getSupabaseStatus(): Promise<any> {
    const response = await api.get('/api/v1/dev/supabase/status');
    return response.data;
  },
};

// Utility functions
export const apiUtils = {
  // Initialize API with Telegram WebApp data
  async initializeWithTelegram(): Promise<User | null> {
    try {
      if (window.Telegram?.WebApp?.initData) {
        const { user } = await authApi.initTelegramAuth(window.Telegram.WebApp.initData);
        return user;
      }
      return null;
    } catch (error) {
      console.error('Failed to initialize with Telegram:', error);
      return null;
    }
  },

  // Upload photo and request estimate
  async uploadPhotoAndEstimate(file: File): Promise<{ photo: FoodPhoto; estimateId: string }> {
    const { photo, upload_url } = await photosApi.createPhoto(file.type);
    await photosApi.uploadToPresignedUrl(upload_url, file);
    const { estimate_id } = await photosApi.requestEstimate(photo.id);

    return { photo, estimateId: estimate_id };
  },

  // Poll for estimate completion
  async pollEstimate(estimateId: string, maxAttempts = 30, interval = 2000): Promise<Estimate> {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const estimate = await estimatesApi.getEstimate(estimateId);

      if (estimate.status === 'done') {
        return estimate;
      }

      if (estimate.status === 'failed') {
        throw new Error('Estimate processing failed');
      }

      await new Promise(resolve => setTimeout(resolve, interval));
    }

    throw new Error('Estimate processing timed out');
  },

  // Format date for API
  formatDate(date: Date): string {
    return date.toISOString().split('T')[0];
  },

  // Get today's date
  getTodayDate(): string {
    return this.formatDate(new Date());
  },

  // Initialize application with configuration, theme, and language detection
  async initializeApplication(): Promise<{
    user: User | null;
    config: UIConfiguration | null;
    theme: ThemeDetectionResponse | null;
    language: LanguageDetectionResponse | null;
  }> {
    try {
      // Initialize Telegram auth first
      const user = await this.initializeWithTelegram();

      // Log application initialization
      await loggingApi.logInfo('Application initialization started', {
        userAuthenticated: !!user,
        userAgent: navigator.userAgent,
        telegramAvailable: !!(window.Telegram?.WebApp),
      });

      // Detect theme and language in parallel
      const [config, theme, language] = await Promise.allSettled([
        configApi.getUIConfiguration(),
        configApi.detectTheme(),
        configApi.detectLanguage(),
      ]);

      const configResult = config.status === 'fulfilled' ? config.value : null;
      const themeResult = theme.status === 'fulfilled' ? theme.value : null;
      const languageResult = language.status === 'fulfilled' ? language.value : null;

      // Log any errors
      if (config.status === 'rejected') {
        await loggingApi.logWarning('Failed to load UI configuration', {
          error: config.reason?.message,
        });
      }
      if (theme.status === 'rejected') {
        await loggingApi.logWarning('Failed to detect theme', {
          error: theme.reason?.message,
        });
      }
      if (language.status === 'rejected') {
        await loggingApi.logWarning('Failed to detect language', {
          error: language.reason?.message,
        });
      }

      await loggingApi.logInfo('Application initialization completed', {
        configLoaded: !!configResult,
        themeDetected: !!themeResult,
        languageDetected: !!languageResult,
      });

      return {
        user,
        config: configResult,
        theme: themeResult,
        language: languageResult,
      };
    } catch (error) {
      await loggingApi.logError('Application initialization failed', {
        error: error instanceof Error ? error.message : String(error),
      });
      throw error;
    }
  },

  // Check application connectivity and health
  async checkApplicationHealth(): Promise<{
    health: boolean;
    connectivity: ConnectivityResponse | null;
    errors: string[];
  }> {
    const errors: string[] = [];
    let health = false;
    let connectivity: ConnectivityResponse | null = null;

    try {
      // Check basic health
      await healthApi.checkHealth();
      health = true;
    } catch (error) {
      errors.push(`Health check failed: ${error instanceof Error ? error.message : String(error)}`);
    }

    try {
      // Check connectivity
      connectivity = await healthApi.checkConnectivity();
    } catch (error) {
      errors.push(`Connectivity check failed: ${error instanceof Error ? error.message : String(error)}`);
    }

    return { health, connectivity, errors };
  },

  // Safe logging function that won't throw errors
  async safeLog(level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL', message: string, context?: Record<string, any>): Promise<void> {
    try {
      switch (level) {
        case 'DEBUG':
          await loggingApi.logDebug(message, context);
          break;
        case 'INFO':
          await loggingApi.logInfo(message, context);
          break;
        case 'WARNING':
          await loggingApi.logWarning(message, context);
          break;
        case 'ERROR':
          await loggingApi.logError(message, context);
          break;
        case 'CRITICAL':
          await loggingApi.logCritical(message, context);
          break;
      }
    } catch (error) {
      // Fallback to console logging if API logging fails
      console.log(`[${level}] ${message}`, context, error);
    }
  },

  // Error boundary logging
  async logComponentError(componentName: string, error: Error, errorInfo?: any): Promise<void> {
    await this.safeLog('ERROR', `Component error in ${componentName}`, {
      error: error.message,
      stack: error.stack,
      errorInfo,
      component: componentName,
    });
  },

  // Performance logging
  async logPerformanceMetric(metric: string, value: number, context?: Record<string, any>): Promise<void> {
    await this.safeLog('INFO', `Performance metric: ${metric}`, {
      metric,
      value,
      unit: 'ms',
      ...context,
    });
  },
};

// Export session manager for use in components
export { sessionManager };

// Debug function to check Telegram WebApp status
export const debugTelegramWebApp = () => {
  const debug = {
    telegramAvailable: !!window.Telegram,
    webAppAvailable: !!window.Telegram?.WebApp,
    initData: window.Telegram?.WebApp?.initData,
    initDataUnsafe: window.Telegram?.WebApp?.initDataUnsafe,
    user: window.Telegram?.WebApp?.initDataUnsafe?.user,
    userId: window.Telegram?.WebApp?.initDataUnsafe?.user?.id,
    storedUser: localStorage.getItem('telegram_user'),
    url: window.location.href,
    userAgent: navigator.userAgent,
    environment: {
      NODE_ENV: process.env.NODE_ENV,
      VITE_ENABLE_DEBUG_LOGGING: import.meta.env.VITE_ENABLE_DEBUG_LOGGING,
      VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL
    }
  };

  console.log('🔍 Telegram WebApp Debug Info:', debug);

  // Also test API call to see if headers are being sent
  console.log('🧪 Testing API call...');
  fetch('/api/v1/goals')
    .then(response => {
      console.log('✅ API call successful:', response.status);
      return response.text();
    })
    .then(data => {
      console.log('📦 API response:', data);
    })
    .catch(error => {
      console.log('❌ API call failed:', error);
    });

  return debug;
};

// Make debug function available globally in development
if (typeof window !== 'undefined') {
  (window as any).debugTelegramWebApp = debugTelegramWebApp;
}

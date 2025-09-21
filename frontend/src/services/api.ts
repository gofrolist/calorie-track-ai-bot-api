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
  user_id: string;
  meal_date: string;
  meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  kcal_total: number;
  macros?: {
    protein_g?: number;
    fat_g?: number;
    carbs_g?: number;
  };
  estimate_id?: string;
  corrected: boolean;
  created_at: string;
  updated_at: string;
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

export interface Goal {
  user_id: string;
  daily_kcal_target: number;
  created_at: string;
  updated_at: string;
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

  async getMealsByDate(date: string): Promise<Meal[]> {
    const response = await api.get('/api/v1/meals', {
      params: { date },
    });
    return response.data;
  },

  async getMealsByDateRange(startDate: string, endDate: string): Promise<Meal[]> {
    const response = await api.get('/api/v1/meals', {
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

// Health API
export const healthApi = {
  async checkHealth(): Promise<{ status: string }> {
    const response = await api.get('/health/live');
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
};

// Export session manager for use in components
export { sessionManager };

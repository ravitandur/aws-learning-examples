import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { AuthTokens } from '../types';

class ApiClient {
  private client: AxiosInstance;
  private tokens: AuthTokens | null = null;

  constructor() {
    this.client = axios.create({
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Load tokens from localStorage on initialization
    this.loadTokensFromStorage();
    this.setupInterceptors();
  }

  private loadTokensFromStorage() {
    try {
      const storedTokens = localStorage.getItem('auth_tokens');
      if (storedTokens) {
        this.tokens = JSON.parse(storedTokens);
      }
    } catch (error) {
      console.error('Error loading tokens from storage:', error);
      this.clearTokens();
    }
  }

  private setupInterceptors() {
    // Request interceptor to add auth header
    this.client.interceptors.request.use(
      (config) => {
        if (this.tokens?.idToken) {
          config.headers.Authorization = `Bearer ${this.tokens.idToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.clearTokens();
          // Redirect to login or dispatch logout event
          window.dispatchEvent(new CustomEvent('auth:unauthorized'));
        }
        return Promise.reject(error);
      }
    );
  }

  public setTokens(tokens: AuthTokens) {
    this.tokens = tokens;
    try {
      localStorage.setItem('auth_tokens', JSON.stringify(tokens));
    } catch (error) {
      console.error('Error storing tokens:', error);
    }
  }

  public clearTokens() {
    this.tokens = null;
    try {
      localStorage.removeItem('auth_tokens');
    } catch (error) {
      console.error('Error clearing tokens:', error);
    }
  }

  public getTokens(): AuthTokens | null {
    return this.tokens;
  }

  public isAuthenticated(): boolean {
    return !!this.tokens?.idToken;
  }

  // Set base URL for different environments
  public setBaseUrl(environment: 'dev' | 'staging' | 'production') {
    const baseUrls = {
      dev: process.env.REACT_APP_API_URL_DEV || 'https://your-api-gateway-dev.execute-api.ap-south-1.amazonaws.com/dev',
      staging: process.env.REACT_APP_API_URL_STAGING || 'https://your-api-gateway-staging.execute-api.ap-south-1.amazonaws.com/staging',
      production: process.env.REACT_APP_API_URL_PROD || 'https://your-api-gateway-prod.execute-api.ap-south-1.amazonaws.com/production'
    };

    this.client.defaults.baseURL = baseUrls[environment];
  }

  // Generic request methods
  public async get<T>(url: string, config?: AxiosRequestConfig) {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  public async post<T>(url: string, data?: any, config?: AxiosRequestConfig) {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  public async put<T>(url: string, data?: any, config?: AxiosRequestConfig) {
    const response = await this.client.put<T>(url, data, config);
    return response.data;
  }

  public async delete<T>(url: string, config?: AxiosRequestConfig) {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }
}

// Create singleton instance
const apiClient = new ApiClient();

// Set default environment (can be overridden)
const environment = (process.env.REACT_APP_ENVIRONMENT as 'dev' | 'staging' | 'production') || 'dev';
apiClient.setBaseUrl(environment);

export default apiClient;
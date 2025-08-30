import axios from 'axios';
import type { AxiosInstance, AxiosResponse } from 'axios';
import { fetchAuthSession } from 'aws-amplify/auth';

class ApiClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor() {
    // Use the same API Gateway endpoint as the custom frontend
    this.baseURL = process.env.NODE_ENV === 'production' 
      ? 'https://your-api-gateway-url.com' 
      : 'https://tuicxyaxlh.execute-api.ap-south-1.amazonaws.com/dev';
    
    this.client = axios.create({
      baseURL: this.baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(async (config) => {
      try {
        const session = await fetchAuthSession();
        const idToken = session.tokens?.idToken?.toString();
        
        if (idToken) {
          config.headers.Authorization = `Bearer ${idToken}`;
        }
      } catch (error) {
        console.error('Error fetching auth session:', error);
      }
      
      return config;
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response: AxiosResponse) => response.data,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized - could trigger re-authentication
          window.dispatchEvent(new Event('auth:unauthorized'));
        }
        return Promise.reject(error);
      }
    );
  }

  async get<T>(url: string): Promise<T> {
    return this.client.get<T>(url);
  }

  async post<T>(url: string, data?: any): Promise<T> {
    return this.client.post<T>(url, data);
  }

  async put<T>(url: string, data?: any): Promise<T> {
    return this.client.put<T>(url, data);
  }

  async delete<T>(url: string): Promise<T> {
    return this.client.delete<T>(url);
  }
}

const apiClient = new ApiClient();
export default apiClient;
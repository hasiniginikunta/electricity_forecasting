import { mockBenchmark, mockBills, mockConsumption, mockForecast, mockHousehold, mockInsights, mockRecommendations, mockRewards, mockUser } from "@/data/mockData";
import type { AuthResponse, Benchmark, Bill, Consumption, Forecast, Household, Insight, Recommendation, Reward, User } from "@/types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";
const SESSION_KEY = "energy-intelligence-session";

const wait = (ms = 180) => new Promise((resolve) => setTimeout(resolve, ms));

async function request<T>(path: string, options: RequestInit = {}, fallback: T): Promise<T> {
  const token = sessionStorage.getItem(SESSION_KEY);
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers },
    });
    if (!response.ok) {
      if (response.status === 401) sessionStorage.removeItem(SESSION_KEY);
      throw { status: response.status, message: "Request failed" };
    }
    return await response.json();
  } catch (error) {
    if (error && typeof error === "object" && "status" in error && (error as { status: number }).status === 401) throw error;
    await wait();
    return fallback;
  }
}

export const authService = {
  async login(email: string, password: string): Promise<AuthResponse> {
    const fallback = { token: "mock-energy-session", userId: mockUser.id, name: mockUser.name };
    return request<AuthResponse>("/api/users/login", { method: "POST", body: JSON.stringify({ email, password }) }, fallback);
  },
  async register(name: string, email: string, password: string): Promise<AuthResponse> {
    const fallback = { token: "mock-energy-session", userId: mockUser.id, name: name || mockUser.name };
    return request<AuthResponse>("/api/users/register", { method: "POST", body: JSON.stringify({ name, email, password }) }, fallback);
  },
};

export const userService = {
  get: (id: number) => request<User>(`/api/users/${id}`, {}, mockUser),
};

export const householdService = {
  get: (id: number) => request<Household>(`/api/households/${id}`, {}, mockHousehold),
  create: (data: Omit<Household, "id">) => request<Household>("/api/households", { method: "POST", body: JSON.stringify(data) }, mockHousehold),
  update: (id: number, data: Omit<Household, "id">) => request<Household>(`/api/households/${id}`, { method: "PUT", body: JSON.stringify(data) }, { ...mockHousehold, ...data }),
};

export const consumptionService = {
  getByHousehold: (id: number) => request<Consumption[]>(`/api/consumption/household/${id}`, {}, mockConsumption),
};

export const billService = {
  getByHousehold: (id: number) => request<Bill[]>(`/api/bills/household/${id}`, {}, mockBills),
};

export const forecastService = {
  getByState: (state: string) => request<Forecast>(`/api/forecasts/state/${state}`, {}, mockForecast),
  getByStateAndDate: (state: string, date: string) => request<Forecast>(`/api/forecasts/state/${state}/date/${date}`, {}, mockForecast),
};

export const benchmarkService = {
  getAll: () => request<Benchmark[]>("/api/benchmarks", {}, [mockBenchmark]),
};

export const insightService = {
  getByHousehold: (id: number) => request<Insight[]>(`/api/insights/household/${id}`, {}, mockInsights),
};

export const rewardService = {
  getByHousehold: (id: number) => request<Reward[]>(`/api/rewards/household/${id}`, {}, mockRewards),
};

export const recommendationService = {
  getAll: () => Promise.resolve(mockRecommendations),
};

export { SESSION_KEY };

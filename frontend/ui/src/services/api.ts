import {
  mockBenchmark, mockBills, mockConsumption, mockForecast,
  mockHousehold, mockInsights, mockRewards, mockUser,
} from "@/data/mockData";
import type {
  AuthResponse, Benchmark, Bill, Consumption, Forecast,
  Household, Insight, Recommendation, Reward, User,
} from "@/types";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";
export const SESSION_KEY = "energy-intelligence-session";

// ── helpers ──────────────────────────────────────────────────────────────────

function getToken(): string | null {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return parsed?.token ?? null;
  } catch {
    return null;
  }
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  fallback: T,
  { useFallback = true } = {},
): Promise<T> {
  const token = getToken();
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    });
    if (!res.ok) {
      if (res.status === 401) sessionStorage.removeItem(SESSION_KEY);
      throw new ApiError(res.status, `HTTP ${res.status}`);
    }
    return await res.json() as T;
  } catch (error) {
    // Always re-throw ApiError (real HTTP errors from the backend)
    if (error instanceof ApiError) throw error;
    // Network/CORS error — only fall back if explicitly allowed
    if (useFallback) return fallback;
    throw error;
  }
}

// Variant that always throws instead of falling back
async function requestStrict<T>(path: string, options: RequestInit = {}): Promise<T> {
  return request<T>(path, options, null as T, { useFallback: false });
}

// ── shape adapters (backend → frontend types) ────────────────────────────────

function adaptConsumption(raw: Record<string, unknown>): Consumption {
  return {
    id: raw.id as number,
    householdId: raw.householdId as number,
    month: (raw.billingMonth ?? raw.month) as string,
    consumptionKwh: (raw.kwhConsumed ?? raw.consumptionKwh) as number,
    changePercent: raw.changePercent as number | undefined,
  };
}

function adaptBill(raw: Record<string, unknown>): Bill {
  return {
    id: raw.id as number,
    householdId: raw.householdId as number,
    month: (raw.billingMonth ?? raw.month) as string,
    amount: (raw.billAmount ?? raw.amount) as number,
    changePercent: raw.changePercent as number | undefined,
  };
}

function adaptForecast(raw: Record<string, unknown>): Forecast {
  return {
    id: raw.id as number,
    state: raw.state as string,
    forecastDate: raw.forecastDate as string,
    demandMw: raw.demandMw as number,
    solarCapacityFactor: raw.solarCapacityFactor as number,
    windCapacityFactor: raw.windCapacityFactor as number,
    netDemandMw: raw.netDemandMw as number,
    renewableShare: raw.renewableShare as number,
    riskLevel: raw.riskLevel as Forecast["riskLevel"],
  };
}

function adaptHousehold(raw: Record<string, unknown>): Household {
  return {
    id: raw.id as number,
    householdSize: raw.householdSize as number,
    city: raw.city as string,
    state: raw.state as string,
    homeType: raw.homeType as Household["homeType"],
  };
}

// ── services ─────────────────────────────────────────────────────────────────

export const authService = {
  login: (email: string, password: string) =>
    requestStrict<AuthResponse>("/api/users/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  register: async (name: string, email: string, password: string): Promise<AuthResponse> => {
    await requestStrict("/api/users/register", { method: "POST", body: JSON.stringify({ name, email, password }) });
    return requestStrict<AuthResponse>("/api/users/login", { method: "POST", body: JSON.stringify({ email, password }) });
  },
};

export const userService = {
  get: (id: number) => request<User>(`/api/users/${id}`, {}, mockUser),
};

export const householdService = {
  getByUserId: async (userId: number): Promise<Household> => {
    const raw = await requestStrict<Record<string, unknown>>(`/api/households/user/${userId}`);
    return adaptHousehold(raw);
  },
  get: async (id: number): Promise<Household> => {
    const raw = await request<Record<string, unknown>>(`/api/households/${id}`, {}, mockHousehold as unknown as Record<string, unknown>);
    return adaptHousehold(raw);
  },
  create: async (data: Omit<Household, "id">): Promise<Household> => {
    const raw = await requestStrict<Record<string, unknown>>("/api/households", { method: "POST", body: JSON.stringify(data) });
    return adaptHousehold(raw);
  },
};

export const consumptionService = {
  getByHousehold: async (id: number): Promise<Consumption[]> => {
    const raw = await request<Record<string, unknown>[]>(`/api/consumption/household/${id}`, {}, mockConsumption as unknown as Record<string, unknown>[]);
    return raw.map(adaptConsumption);
  },
};

export const billService = {
  getByHousehold: async (id: number): Promise<Bill[]> => {
    const raw = await request<Record<string, unknown>[]>(`/api/bills/household/${id}`, {}, mockBills as unknown as Record<string, unknown>[]);
    return raw.map(adaptBill);
  },
};

export const forecastService = {
  getByState: async (state: string): Promise<Forecast> => {
    const raw = await request<Record<string, unknown>[]>(`/api/forecasts/state/${state}`, {}, [mockForecast] as unknown as Record<string, unknown>[]);
    const arr = Array.isArray(raw) ? raw : [raw];
    return adaptForecast(arr[arr.length - 1] ?? (mockForecast as unknown as Record<string, unknown>));
  },
  getByStateAndDate: async (state: string, date: string): Promise<Forecast> => {
    const raw = await request<Record<string, unknown>>(`/api/forecasts/state/${state}/date/${date}`, {}, mockForecast as unknown as Record<string, unknown>);
    return adaptForecast(raw);
  },
};

export const benchmarkService = {
  getAll: () => request<Benchmark[]>("/api/benchmarks", {}, [mockBenchmark]),
  match: (city: string, state: string, householdSizeGroup: string, homeType: string) =>
    request<Benchmark>(`/api/benchmarks/match?city=${encodeURIComponent(city)}&state=${encodeURIComponent(state)}&householdSizeGroup=${encodeURIComponent(householdSizeGroup)}&homeType=${encodeURIComponent(homeType)}`, {}, mockBenchmark),
};

export const insightService = {
  getByHousehold: (id: number) =>
    request<Insight[]>(`/api/insights/household/${id}`, {}, mockInsights),
  generate: (householdId: number) =>
    requestStrict<Insight[]>(`/api/insights/household/${householdId}/generate`, { method: "POST" }),
};

export const rewardService = {
  getByHousehold: (id: number) =>
    request<Reward[]>(`/api/rewards/household/${id}`, {}, mockRewards),
  getBalance: (householdId: number) =>
    request<{ householdId: number; totalCredits: number }>(`/api/rewards/household/${householdId}/balance`, {}, { householdId, totalCredits: mockRewards.reduce((s, r) => s + r.credits, 0) }),
  createChallenge: (data: {
    householdId: number; title: string; description: string;
    targetKwh: number; creditReward: number; startDate: string; endDate: string;
  }) => requestStrict(`/api/rewards/challenges`, { method: "POST", body: JSON.stringify(data) }),
  getChallenges: (householdId: number) =>
    request(`/api/rewards/challenges/household/${householdId}`, {}, []),
  getActiveChallenges: (householdId: number) =>
    request(`/api/rewards/challenges/household/${householdId}/active`, {}, []),
  completeChallenge: (challengeId: number) =>
    requestStrict(`/api/rewards/challenges/${challengeId}/complete`, { method: "POST" }),
  cancelChallenge: (challengeId: number) =>
    requestStrict(`/api/rewards/challenges/${challengeId}/cancel`, { method: "POST" }),
};

export const recommendationService = {
  getAll: (): Promise<Recommendation[]> => Promise.resolve([]),
};

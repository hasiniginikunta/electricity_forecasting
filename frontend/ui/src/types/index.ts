export type HomeType = "FLAT" | "INDEPENDENT_HOUSE";
export type RiskLevel = "LOW" | "MEDIUM" | "HIGH";
export type InsightType = "BENCHMARK" | "SAVING" | "PEAK_USAGE" | "ANOMALY" | "RECOMMENDATION" | "FORECAST";

export interface AuthResponse {
  token: string;
  userId: number;
  name: string;
}

export interface User {
  id: number;
  name: string;
  email: string;
}

export interface Household {
  id: number;
  householdSize: number;
  city: string;
  state: string;
  homeType: HomeType;
}

export interface Consumption {
  id: number;
  householdId: number;
  month: string;
  consumptionKwh: number;
  changePercent?: number;
}

export interface Bill {
  id: number;
  householdId: number;
  month: string;
  amount: number;
  changePercent?: number;
}

export interface Forecast {
  id: number;
  state: string;
  forecastDate: string;
  demandMw: number;
  solarCapacityFactor: number;
  windCapacityFactor: number;
  netDemandMw: number;
  renewableShare: number;
  riskLevel: RiskLevel;
}

export interface Benchmark {
  city: string;
  state: string;
  householdSizeGroup: string;
  homeType: HomeType;
  medianKwh: number;
  p25Kwh: number;
  p75Kwh: number;
  sampleSize: number;
}

export interface Insight {
  id: number;
  householdId: number;
  type: InsightType;
  message: string;
  createdAt: string;
}

export interface Reward {
  id: number;
  householdId: number;
  credits: number;
  reason: string;
  createdAt: string;
}

export interface Recommendation {
  id: number;
  category: "Reduce Consumption" | "Reduce Bill" | "Avoid Peak Usage" | "Improve Efficiency";
  title: string;
  explanation: string;
  savings: number;
  difficulty: "Easy" | "Moderate" | "Advanced";
  icon: "moon" | "snowflake" | "clock" | "plug";
}

export interface ApiError {
  status: number;
  message: string;
}

export interface DashboardData {
  currentUsage: number;
  previousUsage: number;
  currentBill: number;
  predictedBill: number;
  predictedConsumption: number;
  energyScore: number;
  savingsTarget: number;
  savingsProgress: number;
  peakPeriod: string;
  peakUsage: number;
  normalRange: [number, number];
  monthlyConsumption: Array<{ month: string; value: number; bill: number }>;
  timeOfDay: Array<{ label: string; value: number }>;
}

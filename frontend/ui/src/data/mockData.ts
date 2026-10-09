import type { Benchmark, Bill, Consumption, DashboardData, Forecast, Household, Insight, Recommendation, Reward, User } from "@/types";

export const mockUser: User = { id: 1, name: "Alex Kumar", email: "alex@example.com" };
export const mockHousehold: Household = { id: 1, householdSize: 3, city: "Hyderabad", state: "Telangana", homeType: "FLAT" };

export const mockDashboard: DashboardData = {
  currentUsage: 225,
  previousUsage: 210,
  currentBill: 1975,
  predictedBill: 2085,
  predictedConsumption: 238,
  energyScore: 78,
  savingsTarget: 10,
  savingsProgress: 4,
  peakPeriod: "8 PM – 10 PM",
  peakUsage: 74,
  normalRange: [180, 210],
  monthlyConsumption: [
    { month: "May", value: 185, bill: 1640 },
    { month: "Jun", value: 192, bill: 1705 },
    { month: "Jul", value: 205, bill: 1810 },
    { month: "Aug", value: 198, bill: 1750 },
    { month: "Sep", value: 210, bill: 1840 },
    { month: "Oct", value: 225, bill: 1975 },
  ],
  timeOfDay: [
    { label: "Morning", value: 34 },
    { label: "Afternoon", value: 48 },
    { label: "Evening", value: 74 },
  ],
};

export const mockConsumption: Consumption[] = [
  { id: 1, householdId: 1, month: "September", consumptionKwh: 210, changePercent: 0 },
  { id: 2, householdId: 1, month: "October", consumptionKwh: 225, changePercent: 7.1 },
  { id: 3, householdId: 1, month: "August", consumptionKwh: 198, changePercent: -3.4 },
  { id: 4, householdId: 1, month: "July", consumptionKwh: 205, changePercent: 6.8 },
  { id: 5, householdId: 1, month: "June", consumptionKwh: 192, changePercent: -1.9 },
  { id: 6, householdId: 1, month: "May", consumptionKwh: 185, changePercent: -3.6 },
];

export const mockBills: Bill[] = [
  { id: 1, householdId: 1, month: "September", amount: 1840, changePercent: 0 },
  { id: 2, householdId: 1, month: "October", amount: 1975, changePercent: 7.3 },
  { id: 3, householdId: 1, month: "August", amount: 1750, changePercent: -3.3 },
  { id: 4, householdId: 1, month: "July", amount: 1810, changePercent: 6.1 },
  { id: 5, householdId: 1, month: "June", amount: 1705, changePercent: -2.2 },
  { id: 6, householdId: 1, month: "May", amount: 1640, changePercent: -3.8 },
];

export const mockForecast: Forecast = {
  id: 1,
  state: "Telangana",
  forecastDate: "2026-10-07",
  demandMw: 8300,
  solarCapacityFactor: 0.67,
  windCapacityFactor: 0.35,
  netDemandMw: 5100,
  renewableShare: 0.39,
  riskLevel: "MEDIUM",
};

export const mockBenchmark: Benchmark = {
  city: "Hyderabad",
  state: "Telangana",
  householdSizeGroup: "3–4 people",
  homeType: "FLAT",
  medianKwh: 185,
  p25Kwh: 140,
  p75Kwh: 230,
  sampleSize: 1240,
};

export const mockInsights: Insight[] = [
  { id: 1, householdId: 1, type: "BENCHMARK", message: "Your electricity usage is approximately 21.6% higher than similar households in your area.", createdAt: "2026-10-06T18:30:00" },
  { id: 2, householdId: 1, type: "ANOMALY", message: "October usage is higher than your recent pattern. Cooling and evening loads are the likely contributors.", createdAt: "2026-10-05T09:20:00" },
  { id: 3, householdId: 1, type: "PEAK_USAGE", message: "Your highest usage occurs between 8 PM and 10 PM. Shifting appliance use could lower your bill.", createdAt: "2026-10-03T20:15:00" },
  { id: 4, householdId: 1, type: "SAVING", message: "A 10% reduction in consumption could save approximately ₹210 each month.", createdAt: "2026-10-01T12:05:00" },
  { id: 5, householdId: 1, type: "FORECAST", message: "Renewable generation is expected to cover 39% of Telangana demand tomorrow.", createdAt: "2026-09-30T17:45:00" },
];

export const mockRewards: Reward[] = [
  { id: 1, householdId: 1, credits: 100, reason: "Reduced electricity consumption by 10%", createdAt: "2026-10-06T18:30:00" },
  { id: 2, householdId: 1, credits: 75, reason: "Completed 3 energy-saving tips", createdAt: "2026-09-28T11:00:00" },
  { id: 3, householdId: 1, credits: 125, reason: "Avoided peak usage for 7 days", createdAt: "2026-09-20T08:10:00" },
  { id: 4, householdId: 1, credits: 150, reason: "Joined the Energy Intelligence program", createdAt: "2026-08-12T10:00:00" },
];

export const mockRecommendations: Recommendation[] = [
  { id: 1, category: "Avoid Peak Usage", title: "Reduce evening consumption", explanation: "Your highest usage occurs between 8 PM and 10 PM. Run the dishwasher and washing machine earlier when possible.", savings: 120, difficulty: "Easy", icon: "moon" },
  { id: 2, category: "Reduce Bill", title: "Optimize AC usage", explanation: "Set cooling to 24°C and use sleep timers to reduce cooling-related consumption without sacrificing comfort.", savings: 180, difficulty: "Easy", icon: "snowflake" },
  { id: 3, category: "Improve Efficiency", title: "Shift appliance usage", explanation: "Move high-energy appliance usage outside peak hours to flatten your evening load.", savings: 90, difficulty: "Moderate", icon: "clock" },
  { id: 4, category: "Reduce Consumption", title: "Unplug standby devices", explanation: "Entertainment and charging devices are drawing small amounts of power around the clock.", savings: 65, difficulty: "Easy", icon: "plug" },
];

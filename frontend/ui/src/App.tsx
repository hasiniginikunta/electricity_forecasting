import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { AppShell } from "@/layouts/AppShell";
import Dashboard from "@/pages/Dashboard";
import ConsumptionPage from "@/pages/Consumption";
import ForecastPage from "@/pages/Forecast";
import InsightsPage from "@/pages/Insights";
import RecommendationsPage from "@/pages/Recommendations";
import ChallengesPage from "@/pages/Challenges";
import ProfilePage from "@/pages/Profile";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import Onboarding from "@/pages/Onboarding";
import NotFound from "@/pages/NotFound";

const queryClient = new QueryClient();
function ProtectedRoute({ children }: { children: React.ReactNode }) { const { session } = useAuth(); return session ? <>{children}</> : <Navigate to="/login" replace />; }
function PublicRoute({ children }: { children: React.ReactNode }) { const { session } = useAuth(); return session ? <Navigate to="/dashboard" replace /> : <>{children}</>; }

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
            <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />
            <Route path="/onboarding" element={<ProtectedRoute><Onboarding /></ProtectedRoute>} />
            <Route element={<ProtectedRoute><AppShell /></ProtectedRoute>}>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/consumption" element={<ConsumptionPage />} />
              <Route path="/forecast" element={<ForecastPage />} />
              <Route path="/insights" element={<InsightsPage />} />
              <Route path="/recommendations" element={<RecommendationsPage />} />
              <Route path="/challenges" element={<ChallengesPage />} />
              <Route path="/profile" element={<ProfilePage />} />
            </Route>
            <Route path="*" element={<NotFound />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);
export default App;

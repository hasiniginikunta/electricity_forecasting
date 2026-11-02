package org.sergei.backend.service;

import org.sergei.backend.dto.InsightRequest;
import org.sergei.backend.dto.InsightResponse;
import org.sergei.backend.entity.Consumption;
import org.sergei.backend.entity.Household;
import org.sergei.backend.entity.Insight;
import org.sergei.backend.exception.ResourceNotFoundException;
import org.sergei.backend.repository.ConsumptionRepository;
import org.sergei.backend.repository.HouseholdRepository;
import org.sergei.backend.repository.InsightRepository;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Service
public class InsightService {

    // Peak tariff window: 18:00–21:00 (6 PM – 9 PM)
    static final double PEAK_RATE_PER_KWH    = 0.18;
    static final double OFFPEAK_RATE_PER_KWH = 0.10;
    // Fraction of monthly kWh assumed consumed during peak window
    static final double PEAK_FRACTION = 0.30;

    private final InsightRepository insightRepository;
    private final HouseholdRepository householdRepository;
    private final ConsumptionRepository consumptionRepository;
    private final AuthorizationService authorizationService;
    private final MlBridgeService mlBridgeService;

    public InsightService(InsightRepository insightRepository,
                          HouseholdRepository householdRepository,
                          ConsumptionRepository consumptionRepository,
                          AuthorizationService authorizationService,
                          MlBridgeService mlBridgeService) {
        this.insightRepository = insightRepository;
        this.householdRepository = householdRepository;
        this.consumptionRepository = consumptionRepository;
        this.authorizationService = authorizationService;
        this.mlBridgeService = mlBridgeService;
    }

    /** Persist a manually supplied insight. */
    public InsightResponse save(InsightRequest req) {
        authorizationService.requireHouseholdOwnership(req.householdId());
        Household h = householdRepository.findById(req.householdId())
                .orElseThrow(() -> new ResourceNotFoundException(
                        "Household not found: " + req.householdId()));
        Insight i = new Insight();
        i.setHousehold(h);
        i.setType(req.type());
        i.setMessage(req.message());
        return InsightResponse.from(insightRepository.save(i));
    }

    /** Returns stored insights for a household. */
    public List<InsightResponse> getByHousehold(Long householdId) {
        authorizationService.requireHouseholdOwnership(householdId);
        return insightRepository.findByHouseholdIdOrderByCreatedAtDesc(householdId)
                .stream().map(InsightResponse::from).toList();
    }

    /**
     * Generates and persists ML-driven insights for a household:
     *  - Peak usage detection
     *  - Personalised recommendations (anomaly, benchmark, savings target)
     *  - Estimated financial savings
     */
    public List<InsightResponse> generateInsights(Long householdId) {
        authorizationService.requireHouseholdOwnership(householdId);
        Household h = householdRepository.findById(householdId)
                .orElseThrow(() -> new ResourceNotFoundException(
                        "Household not found: " + householdId));

        List<Consumption> history = consumptionRepository
                .findByHouseholdIdOrderByBillingMonthAsc(householdId);

        List<Insight> generated = new ArrayList<>();
        generated.addAll(buildPeakInsights(h, history));
        generated.addAll(buildMlInsights(h));
        generated.addAll(buildSavingsInsights(h, history));

        return insightRepository.saveAll(generated).stream().map(InsightResponse::from).toList();
    }

    // ── Peak Usage Detection ─────────────────────────────────────────────────

    public List<Insight> buildPeakInsights(Household h, List<Consumption> history) {
        List<Insight> insights = new ArrayList<>();
        if (history.isEmpty()) return insights;

        double avgKwh    = history.stream().mapToDouble(Consumption::getKwhConsumed).average().orElse(0);
        double latestKwh = history.get(history.size() - 1).getKwhConsumed();
        double peakKwh   = latestKwh * PEAK_FRACTION;
        double offPeakKwh = latestKwh * (1 - PEAK_FRACTION);

        insights.add(newInsight(h, "PEAK_USAGE", String.format(
                "Peak usage (6 PM–9 PM) accounts for ~%.0f%% of your monthly consumption " +
                "(%.1f kWh peak vs %.1f kWh off-peak, ratio %.2f). " +
                "Shifting heavy appliances to off-peak hours can reduce your bill.",
                PEAK_FRACTION * 100, peakKwh, offPeakKwh, peakKwh / offPeakKwh)));

        if (latestKwh > avgKwh * 1.15) {
            insights.add(newInsight(h, "HIGH_CONSUMPTION", String.format(
                    "Your latest month (%.1f kWh) is %.0f%% above your average (%.1f kWh). " +
                    "Consider auditing high-draw appliances.",
                    latestKwh, ((latestKwh / avgKwh) - 1) * 100, avgKwh)));
        }
        return insights;
    }

    // ── ML-Driven Recommendations ────────────────────────────────────────────

    public List<Insight> buildMlInsights(Household h) {
        List<Insight> insights = new ArrayList<>();
        Map<String, Object> ml = mlBridgeService.runHouseholdInference(
                "H" + String.format("%04d", h.getId()));

        if (ml.containsKey("error")) return insights;

        // Anomaly detection
        Object anomalyRaw = ml.get("anomaly");
        if (anomalyRaw instanceof Map) {
            @SuppressWarnings("unchecked") Map<String, Object> anomaly = (Map<String, Object>) anomalyRaw;
            if (Boolean.TRUE.equals(anomaly.get("detected"))) {
                insights.add(newInsight(h, "ANOMALY",
                        "Unusual consumption detected: " + anomaly.getOrDefault("explanation", "")));
            }
        }

        // Peer benchmark
        Object benchRaw = ml.get("benchmark");
        if (benchRaw instanceof Map) {
            @SuppressWarnings("unchecked") Map<String, Object> bench = (Map<String, Object>) benchRaw;
            if ("available".equals(bench.get("status"))) {
                insights.add(newInsight(h, "BENCHMARK", String.format(
                        "Your consumption is %s vs peers (%.1f%% from median). Peer group: %s households.",
                        bench.getOrDefault("relative_position", "unknown"),
                        toDouble(bench.get("difference_from_median_pct")),
                        bench.getOrDefault("cohort_size", "N/A"))));
            }
        }

        // Savings target → recommendation
        Object savingsRaw = ml.get("savings_target");
        if (savingsRaw instanceof Map) {
            @SuppressWarnings("unchecked") Map<String, Object> savings = (Map<String, Object>) savingsRaw;
            if ("available".equals(savings.get("status"))) {
                double targetPct = toDouble(savings.get("target_percentage"));
                insights.add(newInsight(h, "RECOMMENDATION", String.format(
                        "ML analysis suggests a %.1f%% reduction is achievable. %s",
                        targetPct, savings.getOrDefault("explanation", ""))));
            }
        }

        return insights;
    }

    // ── Financial Savings Estimate ───────────────────────────────────────────

    public List<Insight> buildSavingsInsights(Household h, List<Consumption> history) {
        List<Insight> insights = new ArrayList<>();
        if (history.isEmpty()) return insights;

        double latestKwh = history.get(history.size() - 1).getKwhConsumed();
        double savings   = estimatePeakShiftSavings(latestKwh);

        insights.add(newInsight(h, "SAVINGS_ESTIMATE", String.format(
                "By shifting %.0f%% of peak-hour usage (%.1f kWh) to off-peak, " +
                "you could save approximately $%.2f/month " +
                "(peak rate $%.2f/kWh → off-peak $%.2f/kWh).",
                PEAK_FRACTION * 100, latestKwh * PEAK_FRACTION,
                savings, PEAK_RATE_PER_KWH, OFFPEAK_RATE_PER_KWH)));
        return insights;
    }

    /** savings = peakKwh * (peakRate - offPeakRate) */
    public double estimatePeakShiftSavings(double totalKwh) {
        return totalKwh * PEAK_FRACTION * (PEAK_RATE_PER_KWH - OFFPEAK_RATE_PER_KWH);
    }

    /** savings = totalKwh * reductionPct/100 * offPeakRate */
    public double estimateMlTargetSavings(double totalKwh, double reductionPct) {
        return totalKwh * (reductionPct / 100.0) * OFFPEAK_RATE_PER_KWH;
    }

    private Insight newInsight(Household h, String type, String message) {
        Insight i = new Insight();
        i.setHousehold(h);
        i.setType(type);
        i.setMessage(message);
        return i;
    }

    private double toDouble(Object val) {
        if (val instanceof Number n) return n.doubleValue();
        if (val instanceof String s) {
            try { return Double.parseDouble(s); } catch (NumberFormatException ignored) {}
        }
        return 0.0;
    }
}

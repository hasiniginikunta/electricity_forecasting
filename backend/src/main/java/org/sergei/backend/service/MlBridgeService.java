package org.sergei.backend.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Bridges Java services to Python ML modules via ProcessBuilder.
 * Each call spawns a short-lived Python process that prints JSON to stdout.
 */
@Service
public class MlBridgeService {

    private static final Logger log = LoggerFactory.getLogger(MlBridgeService.class);
    private final ObjectMapper mapper = new ObjectMapper();

    @Value("${ml.python.executable:python3}")
    private String pythonExec;

    @Value("${ml.household-intelligence.dir:../household-intelligence}")
    private String hiDir;

    /**
     * Runs household intelligence inference for a given household.
     * Calls main.py --household_id and parses the JSON output.
     */
    public Map<String, Object> runHouseholdInference(String householdId) {
        return runPython(
                Path.of(hiDir, "main.py").toString(),
                List.of("--household_id", householdId),
                hiDir
        );
    }

    /**
     * Runs the demand/solar/wind forecast script for a given state and date.
     * Calls src/predict.py --state --date and parses the JSON output.
     */
    public Map<String, Object> runForecastInference(String state, String date) {
        return runPython(
                Path.of("../src/predict.py").toString(),
                List.of("--state", state, "--date", date),
                ".."
        );
    }

    private Map<String, Object> runPython(String script, List<String> args, String workDir) {
        try {
            List<String> cmd = new ArrayList<>();
            cmd.add(pythonExec);
            cmd.add(script);
            cmd.addAll(args);

            ProcessBuilder pb = new ProcessBuilder(cmd);
            pb.directory(Path.of(workDir).toAbsolutePath().toFile());
            pb.redirectErrorStream(false);

            Process process = pb.start();
            String stdout = new String(process.getInputStream().readAllBytes());
            String stderr = new String(process.getErrorStream().readAllBytes());
            int exitCode = process.waitFor();

            if (exitCode != 0) {
                log.warn("ML process exited with code {}: {}", exitCode, stderr);
                return Map.of("error", "ml_process_failed", "detail", stderr);
            }

            return mapper.readValue(stdout, new TypeReference<>() {});
        } catch (IOException | InterruptedException e) {
            log.error("ML bridge error: {}", e.getMessage());
            Thread.currentThread().interrupt();
            return Map.of("error", "ml_bridge_unavailable", "detail", e.getMessage());
        }
    }
}

package org.sergei.backend.service;


import org.sergei.backend.dto.BenchmarkRequest;
import org.sergei.backend.dto.BenchmarkResponse;
import org.sergei.backend.entity.Benchmark;
import org.sergei.backend.exception.ResourceNotFoundException;
import org.sergei.backend.repository.BenchmarkRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class BenchmarkService {

    private final BenchmarkRepository benchmarkRepository;
    public BenchmarkService(BenchmarkRepository benchmarkRepository) {
        this.benchmarkRepository = benchmarkRepository;
    }
    public BenchmarkResponse save(BenchmarkRequest req) {
        Benchmark b = new Benchmark();
        b.setCity(req.city());
        b.setState(req.state());
        b.setHouseholdSizeGroup(req.householdSizeGroup());
        b.setHomeType(req.homeType());
        b.setMedianKwh(req.medianKwh());
        b.setP25Kwh(req.p25Kwh());
        b.setP75Kwh(req.p75Kwh());
        b.setSampleSize(req.sampleSize());
        return BenchmarkResponse.from(benchmarkRepository.save(b));
    }

    public List<BenchmarkResponse> getAll() {
        return benchmarkRepository.findAll().stream().map(BenchmarkResponse::from).toList();
    }

    public BenchmarkResponse match(String city, String state, String householdSizeGroup, String homeType) {
        return benchmarkRepository.findByCityAndStateAndHouseholdSizeGroupAndHomeType(city, state, householdSizeGroup, homeType)
                .map(BenchmarkResponse::from)
                .orElseThrow(() -> new ResourceNotFoundException("No benchmark found for the given criteria"));
    }
}

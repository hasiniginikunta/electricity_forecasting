package org.sergei.backend.entity;

import jakarta.persistence.*;

@Entity
@Table(name = "benchmarks",
        uniqueConstraints = @UniqueConstraint(
                name = "uq_benchmarks_segment",
                columnNames = {"city", "state", "household_size_group", "home_type"}))
public class Benchmark {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String city;

    @Column(nullable = false)
    private String state;

    @Column(nullable = false)
    private String householdSizeGroup;

    @Column(nullable = false)
    private String homeType;

    private Double medianKwh;
    private Double p25Kwh;
    private Double p75Kwh;
    private Integer sampleSize;

    public Benchmark() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getCity() { return city; }
    public void setCity(String city) { this.city = city; }

    public String getState() { return state; }
    public void setState(String state) { this.state = state; }

    public String getHouseholdSizeGroup() { return householdSizeGroup; }
    public void setHouseholdSizeGroup(String householdSizeGroup) { this.householdSizeGroup = householdSizeGroup; }

    public String getHomeType() { return homeType; }
    public void setHomeType(String homeType) { this.homeType = homeType; }

    public Double getMedianKwh() { return medianKwh; }
    public void setMedianKwh(Double medianKwh) { this.medianKwh = medianKwh; }

    public Double getP25Kwh() { return p25Kwh; }
    public void setP25Kwh(Double p25Kwh) { this.p25Kwh = p25Kwh; }

    public Double getP75Kwh() { return p75Kwh; }
    public void setP75Kwh(Double p75Kwh) { this.p75Kwh = p75Kwh; }

    public Integer getSampleSize() { return sampleSize; }
    public void setSampleSize(Integer sampleSize) { this.sampleSize = sampleSize; }
}

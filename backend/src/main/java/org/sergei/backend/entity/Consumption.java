package org.sergei.backend.entity;

import jakarta.persistence.*;

@Entity
@Table(name = "consumption",
        uniqueConstraints = @UniqueConstraint(
                name = "uq_consumption_household_month",
                columnNames = {"household_id", "billing_month"}))
public class Consumption {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "household_id", nullable = false)
    private Household household;

    @Column(nullable = false)
    private String billingMonth;

    @Column(nullable = false)
    private Double kwhConsumed;

    public Consumption() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Household getHousehold() { return household; }
    public void setHousehold(Household household) { this.household = household; }

    public String getBillingMonth() { return billingMonth; }
    public void setBillingMonth(String billingMonth) { this.billingMonth = billingMonth; }

    public Double getKwhConsumed() { return kwhConsumed; }
    public void setKwhConsumed(Double kwhConsumed) { this.kwhConsumed = kwhConsumed; }
}

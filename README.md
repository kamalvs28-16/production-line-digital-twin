# LineLens Twin – Production Line Digital Twin & Bottleneck Intelligence

## 🚀 Overview

LineLens Twin is a simulation-based Production Line Digital Twin designed to model a multi-stage manufacturing process and analyze production performance.

The system represents a production line consisting of:

**Cutting → Drilling → Assembly → Inspection**

Using Python and SimPy discrete-event simulation, the application generates simulated production events and analyzes operational performance such as bottlenecks, machine utilization, queue growth, waiting time, throughput, downtime impact, and production delays.

The dashboard also provides What-If Simulation capabilities, allowing users to test operational changes before implementing them on a physical production line.

---

## 🎯 Problem Statement

Manufacturing production lines can experience:

- Bottlenecks
- Machine downtime
- Long queues
- Waiting delays
- Uneven resource utilization
- Throughput reduction
- Production losses

Identifying the impact of these issues before making operational changes can be difficult.

LineLens Twin provides a virtual production environment where different operational scenarios can be simulated and compared.

---

## 💡 Proposed Solution

LineLens Twin creates a virtual representation of a manufacturing production line.

Users can modify production parameters such as:

- Processing time
- Machine capacity
- Parallel machines
- Downtime
- Downtime duration
- Simulation duration

The system then runs a discrete-event simulation and generates performance analytics.

This allows production scenarios to be tested without changing the physical production line.

---

## 🏭 Production Line

```text
Raw Material
     │
     ▼
  Cutting
     │
     ▼
  Drilling
     │
     ▼
  Assembly
     │
     ▼
 Inspection
     │
     ▼
Finished Product
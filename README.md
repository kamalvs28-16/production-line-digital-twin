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

## 🚧 Development Progress

The project was developed incrementally from a production-line simulation into an interactive digital-twin prototype.

### Phase 1 – Production Line Modeling
- Defined the production flow:
  Cutting → Drilling → Assembly → Inspection
- Modeled machines and processing stages using SimPy.
- Introduced processing-time variability.

### Phase 2 – Production Analytics
- Added production event logging.
- Added throughput calculation.
- Added resource utilization analysis.
- Added queue and waiting-time analysis.

### Phase 3 – Bottleneck Intelligence
- Added bottleneck identification.
- Added stage-level performance comparison.
- Added bottleneck delay analysis.

### Phase 4 – Downtime Analysis
- Added machine downtime scenarios.
- Analyzed the effect of downtime on production performance.
- Added downstream delay analysis.

### Phase 5 – What-If Simulation
- Added configurable processing times.
- Added configurable machine capacity.
- Added downtime controls.
- Added baseline vs scenario comparison.

### Phase 6 – Decision Support
- Added rule-based recommendations based on simulated production conditions.

### Phase 7 – Interactive Dashboard
- Integrated the simulation and analytics into a Streamlit dashboard.
- Added interactive charts and production event visualization.
- Added CSV export for simulation results.

### Phase 8 – Documentation and Deployment Preparation
- Added project documentation.
- Added dependency management using `requirements.txt`.
- Added `.gitignore`.
- Prepared the project for GitHub-based collaboration and evaluation.
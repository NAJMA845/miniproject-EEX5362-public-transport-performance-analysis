# Public Transportation Network Simulation

## Overview
This project simulates a **city bus network** to analyze performance metrics such as **passenger waiting times, bus utilization, and throughput**. The goal is to identify bottlenecks, optimize resource usage, and improve passenger satisfaction.

The simulation is implemented using **Python** and **SimPy**, a discrete-event simulation library. It tracks bus movements, passenger arrivals, boarding/alighting, and queue lengths over time.

---

## Features
- **Dynamic Passenger Arrival**: Passengers arrive at stops following an exponential distribution based on specified rates.
- **Bus Operation Simulation**: Multiple buses per route with variable travel times and boarding/alighting durations.
- **Queue Monitoring**: Track queue lengths at each stop over the simulation period.
- **Performance Metrics**:
  - Total passengers served
  - Average, median, and maximum waiting times
  - Passengers served per stop
  - Bus occupancy, utilization, and trips completed
- **Visualization**:
  - Queue length over time per stop
  - Passenger waiting time distribution
- **Data Export**: Generates CSV files:
  - `passengers.csv` – Passenger records
  - `buses.csv` – Bus statistics
  - `queues.csv` – Queue lengths over time

---

## System Description
- **Routes**: Two routes (A & B), each with 3 stops.
- **Bus Capacity**: 40 passengers per bus.
- **Passenger Arrival Rates** (per minute):
  - A1: 0.35, A2: 0.25, A3: 0.20
  - B1: 0.40, B2: 0.30, B3: 0.22
- **Bus Travel Times**: Normally distributed with mean and standard deviation per route.
- **Boarding & Alighting Times**:
  - Boarding: 3 seconds per passenger
  - Alighting: 2 seconds per passenger
- **Simulation Duration**: 8 hours (480 minutes)

---

## Performance Objectives
1. **Reduce Average Waiting Time**: Minimize time passengers wait at stops.
2. **Maximize System Throughput**: Transport as many passengers as possible per hour.
3. **Identify Bottlenecks**: Detect stops or routes with high congestion.
4. **Optimize Resource Utilization**: Efficiently use buses and seats.
5. **Improve On-Time Performance**: Reduce delays and improve schedule adherence.
6. **Enhance Passenger Comfort**: Avoid overcrowding and long queues.

---

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/<your-username>/bus-network-simulation.git
   cd bus-network-simulation

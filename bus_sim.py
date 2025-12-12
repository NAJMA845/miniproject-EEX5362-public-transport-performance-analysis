"""
Public Transportation Network Simulation
Assignment: Performance Modeling and Evaluation
"""

import simpy
import random
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from prettytable import PrettyTable  # pip install prettytable

# -----------------------
# CONFIGURATION
# -----------------------
RANDOM_SEED = 42
SIM_HOURS = 8
SIM_TIME = SIM_HOURS * 60  # minutes

BUS_CAPACITY = 40
BOARDING_TIME = 3 / 60       # 3 seconds per passenger
ALIGHTING_TIME = 2 / 60      # 2 seconds per passenger
MIN_DWELL = 0.1              # minimum dwell time in minutes

# Define routes with stops
ROUTES = {
    "A": {"stops": ["A1", "A2", "A3"], "headway": 15, "num_buses": 2, "travel_mean": 6, "travel_sd": 1},
    "B": {"stops": ["B1", "B2", "B3"], "headway": 12, "num_buses": 2, "travel_mean": 5, "travel_sd": 1}
}

# Passenger arrival rates (per minute)
ARRIVAL_RATES = {"A1": 0.35, "A2": 0.25, "A3": 0.20, "B1": 0.40, "B2": 0.30, "B3": 0.22}

# -----------------------
# DATA COLLECTION
# -----------------------
metrics = {
    "waiting_times": [],
    "passenger_records": [],
    "queue_time_series": {},
    "bus_stats": {},
    "served_per_stop": {}
}

# -----------------------
# ENTITY CLASSES
# -----------------------
class Passenger:
    def __init__(self, pid, arrival_time, origin, destination):
        self.id = pid
        self.arrival_time = arrival_time
        self.origin = origin
        self.destination = destination
        self.board_time = None
        self.alight_time = None

class Stop:
    def __init__(self, env, name):
        self.env = env
        self.name = name
        self.queue = simpy.Store(env)

    def add_passenger(self, passenger):
        return self.queue.put(passenger)

    def get_passenger(self):
        return self.queue.get()

class Bus:
    def __init__(self, env, bus_id, route_name, stops, route_info, start_time=0):
        self.env = env
        self.id = bus_id
        self.route_name = route_name
        self.stops = stops
        self.route_info = route_info
        self.capacity = BUS_CAPACITY
        self.onboard = []
        self.current_index = 0
        self.active_minutes = 0
        self.occupied_minutes = 0
        self.trips_completed = 0
        metrics["bus_stats"][self.id] = {"active_minutes":0, "occupied_minutes":0, "trips_completed":0}
        self.env.process(self.run(start_time))

    def run(self, start_time):
        yield self.env.timeout(start_time)
        while True:
            stop = self.stops[self.current_index]

            # Alighting passengers
            alighting = [p for p in self.onboard if p.destination == stop.name]
            for p in alighting:
                p.alight_time = self.env.now
                self.onboard.remove(p)
            if alighting:
                yield self.env.timeout(len(alighting)*ALIGHTING_TIME)

            # Boarding passengers
            free_space = self.capacity - len(self.onboard)
            boarded = 0
            while free_space > 0 and len(stop.queue.items) > 0:
                p = yield stop.get_passenger()
                p.board_time = self.env.now
                metrics["waiting_times"].append(p.board_time - p.arrival_time)
                self.onboard.append(p)
                metrics["passenger_records"].append({
                    "id":p.id, "origin":p.origin, "destination":p.destination,
                    "arrival":p.arrival_time, "board":p.board_time, "alight":p.alight_time,
                    "route":self.route_name, "bus":self.id
                })
                # Count per stop
                if stop.name not in metrics["served_per_stop"]:
                    metrics["served_per_stop"][stop.name] = 0
                metrics["served_per_stop"][stop.name] += 1

                boarded +=1
                free_space -=1
                yield self.env.timeout(BOARDING_TIME)

            # Minimum dwell if no boarding/alighting
            if boarded==0 and len(alighting)==0:
                yield self.env.timeout(MIN_DWELL)

            # Travel to next stop
            travel_time = max(0.5, random.gauss(self.route_info["travel_mean"], self.route_info["travel_sd"]))
            t = travel_time
            while t>0:
                step = min(1, t)
                self.active_minutes += step
                self.occupied_minutes += len(self.onboard)*step
                metrics["bus_stats"][self.id]["active_minutes"] += step
                metrics["bus_stats"][self.id]["occupied_minutes"] += len(self.onboard)*step
                yield self.env.timeout(step)
                t -= step

            # Move to next stop
            self.current_index = (self.current_index + 1) % len(self.stops)
            if self.current_index==0:
                self.trips_completed +=1
                metrics["bus_stats"][self.id]["trips_completed"] +=1

# -----------------------
# PASSENGER GENERATOR
# -----------------------
def passenger_generator(env, stop, rate, route_stops):
    pid = 0
    while True:
        interarrival = np.random.exponential(1/rate)
        yield env.timeout(interarrival)
        pid +=1
        idx = route_stops.index(stop.name)
        dest = random.choice(route_stops[idx+1:]) if idx+1<len(route_stops) else stop.name
        p = Passenger(f"{stop.name}-{pid}", env.now, stop.name, dest)
        stop.add_passenger(p)

# -----------------------
# MONITOR QUEUES
# -----------------------
def monitor(env, stops):
    while True:
        for s in stops.values():
            if s.name not in metrics["queue_time_series"]:
                metrics["queue_time_series"][s.name]=[]
            metrics["queue_time_series"][s.name].append((env.now, len(s.queue.items)))
        yield env.timeout(1)

# -----------------------
# SIMULATION SETUP
# -----------------------
def run_simulation():
    env = simpy.Environment()
    # Create stops
    stops_map = {}
    for route in ROUTES.values():
        for s in route["stops"]:
            stops_map[s] = Stop(env, s)

    # Start passenger generators
    for sname, lam in ARRIVAL_RATES.items():
        for r in ROUTES.values():
            if sname in r["stops"]:
                env.process(passenger_generator(env, stops_map[sname], lam, r["stops"]))
                break

    # Start buses
    for route_name, rinfo in ROUTES.items():
        for i in range(rinfo["num_buses"]):
            start_offset = i*rinfo["headway"]/rinfo["num_buses"]
            Bus(env, f"{route_name}-Bus-{i+1}", route_name, [stops_map[s] for s in rinfo["stops"]], rinfo, start_time=start_offset)

    # Start monitor
    env.process(monitor(env, stops_map))
    env.run(until=SIM_TIME)

    # -----------------------
    # POST SIMULATION STATISTICS
    # -----------------------
    print("\n=== Simulation Complete ===\n")

    # Waiting time stats
    total_passengers = len(metrics['passenger_records'])
    avg_wait = np.mean(metrics['waiting_times'])
    median_wait = np.median(metrics['waiting_times'])
    max_wait = np.max(metrics['waiting_times'])
    print(f"Total passengers served: {total_passengers}")
    print(f"Average waiting time: {avg_wait:.2f} min")
    print(f"Median waiting time: {median_wait:.2f} min")
    print(f"Maximum waiting time: {max_wait:.2f} min\n")

    # Served per stop table
    table1 = PrettyTable()
    table1.field_names = ["Stop", "Passengers Served"]
    for stop, count in metrics["served_per_stop"].items():
        table1.add_row([stop, count])
    print("Passengers Served Per Stop:")
    print(table1)

    # Bus summary table
    table2 = PrettyTable()
    table2.field_names = ["Bus ID", "Route", "Active min", "Occupied min", "Trips", "Avg Occupancy", "Utilization %"]
    for bus, stat in metrics["bus_stats"].items():
        avg_occ = stat["occupied_minutes"]/stat["active_minutes"] if stat["active_minutes"]>0 else 0
        util = (stat["occupied_minutes"]/(stat["active_minutes"]*BUS_CAPACITY))*100 if stat["active_minutes"]>0 else 0
        table2.add_row([bus, bus.split("-")[0], round(stat["active_minutes"],2), round(stat["occupied_minutes"],2),
                        stat["trips_completed"], round(avg_occ,2), round(util,2)])
    print("\nBus Summary:")
    print(table2)

    # -----------------------
    # SAVE CSV FILES
    # -----------------------
    pd.DataFrame(metrics["passenger_records"]).to_csv("passengers.csv", index=False)
    pd.DataFrame([{**{"Bus":k}, **v} for k,v in metrics["bus_stats"].items()]).to_csv("buses.csv", index=False)

    # Queue CSV
    queue_data = []
    for stop, series in metrics["queue_time_series"].items():
        for t, q in series:
            queue_data.append({"Time":t, "Stop":stop, "Queue Length":q})
    pd.DataFrame(queue_data).to_csv("queues.csv", index=False)

    print("\nCSV files saved: passengers.csv, buses.csv, queues.csv\n")

    # -----------------------
    # PLOTS
    # -----------------------
    # Queue lengths over time
    plt.figure(figsize=(10,5))
    for stop, series in metrics["queue_time_series"].items():
        times = [t for t,_ in series]
        qlens = [q for _,q in series]
        plt.plot(times, qlens, label=stop)
    plt.xlabel("Time (minutes)")
    plt.ylabel("Queue length")
    plt.title("Queue Lengths at Stops Over Time")
    plt.legend()
    plt.grid(True)
    plt.show()

    # Waiting time histogram
    plt.figure(figsize=(8,4))
    plt.hist(metrics["waiting_times"], bins=30, color="skyblue")
    plt.xlabel("Waiting Time (min)")
    plt.ylabel("Frequency")
    plt.title("Passenger Waiting Time Distribution")
    plt.grid(True)
    plt.show()

# -----------------------
# RUN SIMULATION
# -----------------------
run_simulation()

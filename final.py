import matplotlib.pyplot as plt
import airlines
from itertools import product

# Define the timezone of each airport
airport_timezone = {
    "ATL": "ET", "BOS": "ET", "BWI": "ET", "CLT": "ET", "DCA": "ET", "DTW": "ET",
    "EWR": "ET", "FLL": "ET", "IAD": "ET", "JFK": "ET", "LGA": "ET", "MCO": "ET",
    "MIA": "ET", "PHL": "ET", "TPA": "ET",
    "ORD": "CT", "MDW": "CT", "DFW": "CT", "IAH": "CT", "MSP": "CT",
    "DEN": "MT", "PHX": "MT", "SLC": "MT",
    "LAX": "PT", "LAS": "PT", "SFO": "PT", "SAN": "PT", "SEA": "PT", "PDX": "PT"
}

# Geographic coordinates for plotting (longitude, latitude)
airport_coords = {
    "ATL": (-84.43, 33.64), "BOS": (-71.01, 42.36), "BWI": (-76.67, 39.18), "CLT": (-80.94, 35.21),
    "DCA": (-77.04, 38.85), "DTW": (-83.36, 42.21), "EWR": (-74.17, 40.69), "FLL": (-80.15, 26.07),
    "IAD": (-77.46, 38.95), "JFK": (-73.78, 40.64), "LGA": (-73.87, 40.77), "MCO": (-81.31, 28.43),
    "MIA": (-80.29, 25.79), "PHL": (-75.24, 39.87), "TPA": (-82.53, 27.97),
    "ORD": (-87.91, 41.97), "MDW": (-87.75, 41.79), "DFW": (-97.04, 32.90), "IAH": (-95.34, 29.98), "MSP": (-93.21, 44.88),
    "DEN": (-104.67, 39.86), "PHX": (-112.01, 33.43), "SLC": (-111.98, 40.79),
    "LAX": (-118.41, 33.94), "LAS": (-115.15, 36.08), "SFO": (-122.38, 37.62), "SAN": (-117.16, 32.73),
    "SEA": (-122.31, 47.45), "PDX": (-122.59, 45.59)
}

# Define which timezones are considered adjacent
timezone_neighbors = {
    "ET": {"CT"},
    "CT": {"ET", "MT"},
    "MT": {"CT", "PT"},
    "PT": {"MT"}
}

# Load and preprocess data
data = airlines.get_airports()
airport_months = {}
delay_by_airport = {}

for record in data:
    code = record["Airport"]["Code"]
    if code not in airport_timezone:
        continue
    time = (record["Time"]["Year"], record["Time"]["Month"])
    total_delay = record["Statistics"]["Minutes Delayed"]["Total"]
    delayed_flights = record["Statistics"]["Flights"]["Delayed"]
    if code not in airport_months:
        airport_months[code] = set()
        delay_by_airport[code] = {}
    airport_months[code].add(time)
    delay_by_airport[code][time] = total_delay / delayed_flights if delayed_flights > 0 else 0.0

# Manually build the graph using adjacency timezones
graph = {}
airports = list(airport_timezone.keys())
for a1, a2 in product(airports, repeat=2):
    if a1 == a2:
        continue
    tz1, tz2 = airport_timezone[a1], airport_timezone[a2]
    if tz1 == tz2 or tz2 not in timezone_neighbors.get(tz1, set()):
        continue
    common = airport_months[a1] & airport_months[a2]
    if common:
        delays = [delay_by_airport[a1][m] for m in common]
        avg_delay = sum(delays) / len(delays)
        graph.setdefault(a1, []).append((a2, avg_delay))

# Handwritten Dijkstra's algorithm to find shortest path
def dijkstra(graph, start, end):
    dist = {node: float('inf') for node in graph}
    prev = {node: None for node in graph}
    dist[start] = 0
    unvisited = set(graph)

    while unvisited:
        curr = min((n for n in unvisited if dist[n] < float('inf')), key=lambda n: dist[n], default=None)
        if curr is None or curr == end:
            break
        unvisited.remove(curr)
        for neighbor, weight in graph.get(curr, []):
            new_dist = dist[curr] + weight
            if new_dist < dist.get(neighbor, float('inf')):
                dist[neighbor] = new_dist
                prev[neighbor] = curr

    # Backtrack from destination to reconstruct the path
    path = []
    node = end
    while node:
        path.append(node)
        node = prev.get(node)
    path.reverse()
    return path, dist[end] if dist[end] != float('inf') else None

# User input
print("Available airports:")
print(", ".join(sorted(airports)))
start = input("Enter start airport code: ").strip().upper()
end = input("Enter destination airport code: ").strip().upper()

# Run and visualize results
if start not in graph or end not in graph:
    print("Invalid airport code.")
else:
    path, delay = dijkstra(graph, start, end)
    if delay is None or len(path) == 0:
        print("No path found.")
    else:
        print(f"\nPath from {start} to {end}:")
        print(" → ".join(path))
        print(f"Total estimated delay: {round(delay, 2)} minutes")

        # Visualize the graph and path
        plt.figure(figsize=(13, 8))

        # Draw all connections in gray
        for a1 in graph:
            for a2, _ in graph[a1]:
                x = [airport_coords[a1][0], airport_coords[a2][0]]
                y = [airport_coords[a1][1], airport_coords[a2][1]]
                plt.plot(x, y, color='gray', linewidth=0.5)

        # Draw the shortest path with red arrows
        for i in range(len(path) - 1):
            a1, a2 = path[i], path[i + 1]
            plt.annotate("",
                xy=airport_coords[a2],
                xytext=airport_coords[a1],
                arrowprops=dict(arrowstyle="->", color="red", lw=2.5),
            )

        # Draw airport nodes
        for code, (x, y) in airport_coords.items():
            plt.scatter(x, y, color='skyblue', s=300)
            plt.text(x, y, code, fontsize=9, ha='center', va='center', color='black')

        # Title includes path and delay
        title_path = " → ".join(path)
        plt.title(f"Route: {title_path}\nEstimated Delay: {round(delay, 2)} minutes", fontsize=14)
        plt.axis('off')
        plt.show()
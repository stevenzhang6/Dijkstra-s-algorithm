import airlines
from itertools import product

# Airport to timezone mapping
airport_timezone = {
    "ATL": "ET", "BOS": "ET", "BWI": "ET", "CLT": "ET", "DCA": "ET", "DTW": "ET",
    "EWR": "ET", "FLL": "ET", "IAD": "ET", "JFK": "ET", "LGA": "ET", "MCO": "ET",
    "MIA": "ET", "PHL": "ET", "TPA": "ET",
    "ORD": "CT", "MDW": "CT", "DFW": "CT", "IAH": "CT", "MSP": "CT",
    "DEN": "MT", "PHX": "MT", "SLC": "MT",
    "LAX": "PT", "LAS": "PT", "SFO": "PT", "SAN": "PT", "SEA": "PT", "PDX": "PT"
}

# Define adjacent timezones
timezone_neighbors = {
    "ET": {"CT"},
    "CT": {"ET", "MT"},
    "MT": {"CT", "PT"},
    "PT": {"MT"}
}

# Load and process data
data = airlines.get_airports()
airport_months = {}
delay_by_airport = {}

for record in data:
    airport = record["Airport"]["Code"]
    if airport not in airport_timezone:
        continue

    time = (record["Time"]["Year"], record["Time"]["Month"])
    total_delay = record["Statistics"]["Minutes Delayed"]["Total"]
    delayed_flights = record["Statistics"]["Flights"]["Delayed"]

    if airport not in airport_months:
        airport_months[airport] = set()
    if airport not in delay_by_airport:
        delay_by_airport[airport] = {}

    airport_months[airport].add(time)
    delay_by_airport[airport][time] = total_delay / delayed_flights if delayed_flights > 0 else 0.0

# Build graph using timezone restriction
graph = {}
airports = list(airport_months.keys())

for a1, a2 in product(airports, repeat=2):
    if a1 == a2:
        continue
    tz1 = airport_timezone[a1]
    tz2 = airport_timezone[a2]
    if tz2 != tz1 and tz2 not in timezone_neighbors.get(tz1, set()):
        continue

    common_months = airport_months[a1] & airport_months[a2]
    if common_months:
        delays = [delay_by_airport[a1][month] for month in common_months]
        avg_delay = sum(delays) / len(delays)
        if a1 not in graph:
            graph[a1] = []
        graph[a1].append((a2, avg_delay))

# Dijkstra's algorithm
def dijkstra(graph, start, end):
    distances = {node: float('inf') for node in graph}
    previous = {node: None for node in graph}
    distances[start] = 0
    unvisited = set(graph.keys())

    while unvisited:
        current = min(
            (node for node in unvisited if distances[node] != float('inf')),
            key=lambda node: distances[node],
            default=None
        )
        if current is None or current == end:
            break
        unvisited.remove(current)

        for neighbor, weight in graph.get(current, []):
            if neighbor not in distances:
                distances[neighbor] = float('inf')
                previous[neighbor] = None
            new_dist = distances[current] + weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                previous[neighbor] = current

    path = []
    node = end
    while node:
        path.append(node)
        node = previous.get(node)
    path.reverse()

    return path, distances[end] if distances[end] != float('inf') else None

# User input
print("Available airport codes:")
print(", ".join(sorted(graph.keys())))

start = input("\nEnter departure airport code: ").strip().upper()
end = input("Enter destination airport code: ").strip().upper()

if start not in graph or end not in graph:
    print("\nOne or both airport codes are invalid or not in the network.")
else:
    path, delay = dijkstra(graph, start, end)
    if delay is not None:
        print(f"\nLeast-delayed path from {start} to {end}:")
        print(" → ".join(path))
        print(f"Estimated total delay (avg per delayed flight): {round(delay, 2)} minutes")
        print(f"You will pass through {len(path)} airport(s):")
        print(f"    Start at {path[0]}")
        if len(path) > 2:
            print(f"    Then via: {', '.join(path[1:-1])}")
        if len(path) > 1:
            print(f"    Arrive at {path[-1]}")
    else:
        print("\nNo path found between", start, "and", end)
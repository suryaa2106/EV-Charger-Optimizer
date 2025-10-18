import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(layout="wide", page_title="⚡ EV Charging Optimizer + Advisor")

# Helper: build graph
def parse_edges(text):
    G = nx.Graph()
    for line in text.splitlines():
        line = line.strip()
        if not line: 
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        u, v, w = parts[0], parts[1], float(parts[2])
        G.add_node(u); G.add_node(v)
        G.add_edge(u, v, weight=w)
    return G

# Visualization
def draw_graph(G, chargers=set(), new=set(), path=None, recharge_nodes=None, highlight_node=None, title="Graph"):
    plt.figure(figsize=(6,5))
    pos = nx.spring_layout(G, seed=42)
    node_colors = []
    for n in G.nodes:
        if highlight_node and n == highlight_node:
            node_colors.append("#d291bc")  
        elif recharge_nodes and n in recharge_nodes:
            node_colors.append("#f28585")  
        elif n in new:
            node_colors.append("#ffb347")  
        elif n in chargers:
            node_colors.append("#66c2a5")  
        else:
            node_colors.append("#89CFF0")  
    nx.draw(G, pos, with_labels=True, node_color=node_colors, node_size=800, font_size=10)
    edge_labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=9)
    if path:
        edges_in_path = list(zip(path, path[1:]))
        nx.draw_networkx_edges(G, pos, edgelist=edges_in_path, edge_color='red', width=3)
    plt.title(title)
    st.pyplot(plt.gcf())
    plt.clf()

# K-center
def k_center_with_existing(G, k_new, existing_chargers):
    nodes = list(G.nodes)
    centers = list(existing_chargers)[:] if existing_chargers else [nodes[0]]
    while len(centers) < (len(existing_chargers) + k_new):
        max_dist, far_node = -1, None
        for n in nodes:
            dists = []
            for c in centers:
                try:
                    d = nx.shortest_path_length(G, n, c, weight="weight")
                except nx.NetworkXNoPath:
                    d = float('inf')
                dists.append(d)
            min_dist = min(dists)
            if min_dist > max_dist:
                max_dist = min_dist
                far_node = n
        if far_node is None:
            break
        centers.append(far_node)
    return [c for c in centers if c not in existing_chargers]


# Battery-safe routing
def battery_safe_route(G, source, target, battery_capacity, initial_battery, chargers_set):
    import heapq
    pq = [(0.0, source, initial_battery, [source], [])]
    visited = set()
    while pq:
        cost, node, battery, path, recharges = heapq.heappop(pq)
        key = (node, round(battery,1))
        if key in visited:
            continue
        visited.add(key)

        if node == target:
            avg_km = cost / (len(recharges) + 1) if recharges else cost
            return path, cost, recharges, avg_km

        if node in chargers_set and node != source:
            battery = battery_capacity
            if node not in recharges:
                recharges = recharges + [node]

        for nb in G.neighbors(node):
            dist = G[node][nb]['weight']
            if battery >= dist:
                new_cost = cost + dist
                new_battery = battery - dist
                heapq.heappush(pq, (new_cost, nb, new_battery, path + [nb], recharges[:]))
    return None, float('inf'), [], None


# Station decision (dynamic)
def station_decision(distance_to_station, distance_to_next, current_battery, evs_waiting, station_capacity, charge_time, battery_capacity):
    if current_battery < distance_to_station:
        return "❌ Cannot reach this station."
    battery_after_station = current_battery - distance_to_station
    wait_time_here = (evs_waiting / station_capacity) * charge_time if station_capacity > 0 else float('inf')
    total_time_here = wait_time_here + charge_time
    can_skip = battery_after_station >= distance_to_next
    if not can_skip:
        return f"⚡ Must stop. Wait ≈ {round(wait_time_here)} min."
    if wait_time_here < charge_time:
        return f"👍 Better to stop here. Wait ≈ {round(wait_time_here)} min."
    else:
        return f"➡️ Better to skip. Next station {distance_to_next} km ahead. Battery left after reaching = {battery_after_station - distance_to_next}."


# STREAMLIT UI
st.title("⚡ EV Charging Network Optimizer + Range Anxiety + Dynamic Convoy Advisor")

with st.sidebar.expander("1) Graph input"):
    st.markdown("Enter edges: `A B 40`")
    default = "A B 40\nB C 20\nC D 25\nB E 30\nE F 20"
    edges_text = st.text_area("Edges (u v weight)", value=default, height=140)
    G = parse_edges(edges_text)

nodes = list(G.nodes)
if not nodes:
    st.warning("Graph empty — enter edges.")
    st.stop()

with st.sidebar.expander("2) Charging stations"):
    chargers = st.multiselect("Select existing chargers", nodes, default=["B","C","E"])
    station_capacity = st.number_input("Chargers per station", 1, 10, 2)
    charge_time = st.number_input("Charging time per EV (min)", 10, 180, 30)

with st.sidebar.expander("3) Battery setup"):
    battery_capacity = st.slider("Battery capacity (km)", 10, 500, 100)
    initial_battery = st.slider("Initial battery (km)", 0, battery_capacity, 60)

with st.sidebar.expander("4) K-center optimization"):
    k_new = st.number_input("New stations to add (k)", 0, len(nodes), 1)
    if st.button("Run K-center"):
        new_centers = k_center_with_existing(G, k_new, set(chargers))
        st.session_state['new_centers'] = new_centers
        st.success(f"Suggested new stations: {new_centers}")

new_centers = st.session_state.get('new_centers', [])

st.markdown("---")
tab1, tab2, tab3 = st.tabs(["📊 Graph", "🔋 Range Anxiety", "🚗 Convoy Advisor"])


# TAB 1: Graph + Optimizer
with tab1:
    st.subheader("Network Graph with Chargers")
    draw_graph(G, chargers=set(chargers), new=set(new_centers), title="EV Network")
    st.write("Nodes:", nodes)
    st.write("Existing chargers:", chargers)
    st.write("New (K-center):", new_centers)
    st.table([{"u":u,"v":v,"dist":G[u][v]['weight']} for u,v in G.edges])


# TAB 2: Range Anxiety
with tab2:
    st.subheader("Battery-Safe Route")
    src = st.selectbox("Source", nodes, index=0)
    dst = st.selectbox("Destination", nodes, index=max(0,len(nodes)-1))
    if st.button("Find Safe Route"):
        chargers_set = set(chargers) | set(new_centers)
        path, dist, recharges, avg_km = battery_safe_route(G, src, dst, battery_capacity, initial_battery, chargers_set)
        if not path:
            st.error("No safe path.")
        else:
            st.success(f"Path: {' → '.join(path)} (distance {dist} km)")
            if recharges:
                st.info(f"Recharge stops: {', '.join(recharges)}")
            st.write(f"Average distance per recharge ≈ {round(avg_km,1)} km")
            draw_graph(G, chargers=set(chargers), new=set(new_centers), path=path, recharge_nodes=recharges, title="Safe Route")


# TAB 3: Convoy Advisor (Decision)
with tab3:
    st.subheader("Dynamic Station Decision")
    if 'path' not in locals():
        st.info("Run Range Anxiety tab first to get a path.")
    else:
        waiting_info = {}
        st.write("Enter EVs already waiting at each charger:")
        for ch in chargers:
            waiting_info[ch] = st.number_input(f"EVs waiting at {ch}", 0, 20, 2, key=f"wait_{ch}")

        st.write("📍 Decisions at stations along path:")
        for i, node in enumerate(path):
            if node in chargers and node != dst:
                dist_to_here = sum(G[path[j]][path[j+1]]['weight'] for j in range(i))
                dist_to_next = G[path[i]][path[i+1]]['weight'] if i+1 < len(path) else float('inf')
                decision = station_decision(dist_to_here, dist_to_next, initial_battery, waiting_info[node], station_capacity, charge_time, battery_capacity)
                st.write(f"At Station {node}: {decision}")

# ⚡ EV Charging Network Optimizer + Advisor

A **Streamlit web app** to optimize electric vehicle (EV) charging networks, plan battery-safe routes, and give dynamic convoy advice for EVs. Visualize a road network, locate optimal charging stations, and make informed charging decisions.

---

## Features

1. **Network Graph Visualization**  
   - Enter road segments with distances (`A B 40`)  
   - Display existing and suggested charging stations  
   - Highlight battery-safe routes

2. **K-Center Optimization**  
   - Suggests optimal locations for new charging stations to minimize maximum distance to nearest station  
   - Considers existing stations

3. **Battery-Safe Routing**  
   - Finds EV routes ensuring the battery doesn't deplete  
   - Shows recharge stops  
   - Calculates average distance per recharge

4. **Dynamic Convoy Advisor**  
   - Provides recommendations at each station along a route  
   - Considers battery level, distance to next station, charging time, and EV queue

---

## Demo

![Demo Screenshot](./screenshot.png) 

---

## Installation

1. Clone the repo:

```bash
git clone https://github.com/yourusername/ev-charging-optimizer.git
cd ev-charging-optimizer

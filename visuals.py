import folium
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from config import OUTPUT_DIR

class Visualizer:
    @staticmethod
    def create_map(results):
        m = folium.Map(location=[30.5, 79.4], zoom_start=9, tiles='CartoDB positron')
        
        for r in results:
            popup = f"<b>{r['icon']} {r['name']}</b><br>Risk: {r['risk_level']} ({r['risk_score']})<br>Evacuate: {r['people_at_risk']} people"
            folium.CircleMarker([r['lat'], r['lon']], radius=12, color=r['color'], fill=True, popup=popup).add_to(m)
            
        path = f"{OUTPUT_DIR}/map.html"
        m.save(path)
        return path

    @staticmethod
    def create_chart(results):
        names = [r['name'] for r in results]
        scores = [r['risk_score'] for r in results]
        colors = [r['color'] for r in results]
        
        plt.figure(figsize=(10, 5))
        plt.bar(names, scores, color=colors)
        plt.title("Flood Risk Scores")
        plt.ylabel("Risk Score (0-100)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        path = f"{OUTPUT_DIR}/chart.png"
        plt.savefig(path)
        plt.close()
        return path
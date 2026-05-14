import os
import json
import numpy as np
from sklearn.cluster import KMeans
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Error: OPENAI_API_KEY not found in .env file.")

client = OpenAI(api_key=api_key)

def load_data(filepath):
    records = []
    if not os.path.exists(filepath):
        print(f"File {filepath} not found.")
        return records
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                rec = json.loads(line)
                # Ensure it has an embedding
                if rec.get("Embedding"):
                    records.append(rec)
            except:
                pass
    return records

from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

@retry(
    retry=retry_if_exception_type(Exception),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(5)
)
def generate_theme_name(samples):
    prompt = f"""
    You are a Senior Marine Investigator. I have clustered similar marine incidents together based on their underlying latent causes.
    Here are the pattern discovery summaries for several incidents in one cluster:
    
    {json.dumps(samples, indent=2)}
    
    Please provide:
    1. A short, professional Theme Title (e.g., "Autopilot Sensor Degradation during Mooring").
    2. A 1-2 paragraph professional summary explaining what this theme is, why it occurs, and how weather or other latent factors play a role based on the samples.
    
    Format:
    ### [Theme Title]
    [Summary]
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def generate_report():
    print("Loading analyzed incidents...")
    records = load_data("analyzed_incidents.jsonl")
    if not records:
         print("No records found to cluster.")
         return
         
    print(f"Loaded {len(records)} records with embeddings.")
    
    # Extract embeddings
    embeddings = [r["Embedding"] for r in records]
    X = np.array(embeddings)
    
    # Determine number of clusters (min 2, max 10 depending on data size)
    n_clusters = min(7, max(2, len(records) // 10))
    print(f"Clustering into {n_clusters} themes using K-Means...")
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
    labels = kmeans.fit_predict(X)
    
    # Group records by cluster
    clusters = {i: [] for i in range(n_clusters)}
    for idx, label in enumerate(labels):
        clusters[label].append(records[idx])
        
    report = "# Marine Accident Thematic Analysis Report\n\n"
    report += "This report outlines discovered macro-themes derived from unstructured marine incident reports. The themes were clustered mathematically using embeddings and synthesized by GPT-4o.\n\n"
    
    for i in range(n_clusters):
        print(f"Generating summary for cluster {i+1}/{n_clusters}...")
        cluster_records = clusters[i]
        
        # We can sort them or just pick 5 random to give context to the LLM to save tokens
        samples = []
        for r in cluster_records[:min(5, len(cluster_records))]:
             samples.append({
                  "weather": r.get("Meteostat_Weather"),
                  "analysis": r.get("Analysis")
             })
             
        theme_summary = generate_theme_name(samples)
        
        lines = theme_summary.split('\n')
        for idx, line in enumerate(lines):
             if line.strip().startswith('###'):
                  lines[idx] = f"{line.strip()} *(Exhibited in {len(cluster_records)} incidents)*"
                  break
        theme_summary = '\n'.join(lines)
        
        report += f"{theme_summary}\n\n"
        report += "**Representative Cases:**\n"
        for r in cluster_records[:3]:
             occ_id = r.get("Occurrence_Id")
             cause = r.get("Analysis", {}).get("explicit_cause_reported", "N/A")
             report += f"- **Occurrence {occ_id}**: {cause}\n"
        
        report += "\n---\n\n"
        
    with open("marine_accident_themes_analysis.md", "w", encoding='utf-8') as f:
         f.write(report)
         
    print("Report generated: marine_accident_themes_analysis.md")

if __name__ == "__main__":
    generate_report()

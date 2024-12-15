# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas",
#   "matplotlib",
#   "seaborn",
#   "requests",
#   "openai",
#   "tenacity",
# ]
# ///
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

# Set the AI Proxy token from environment variable
AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")
if not AIPROXY_TOKEN:
    raise ValueError("AIPROXY_TOKEN environment variable not set.")

API_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"

# Retry logic for API calls
@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5))
def ask_gpt(prompt):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AIPROXY_TOKEN}"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(API_URL, headers=headers, json=data)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
def load_csv(file_path):
    try:
        # Attempt to load with UTF-8
        data = pd.read_csv(file_path, encoding="utf-8")
    except UnicodeDecodeError:
        print("UTF-8 decoding failed. Retrying with 'latin1' encoding.")
        try:
            # Retry with latin1 encoding
            data = pd.read_csv(file_path, encoding="latin1")
        except Exception as e:
            raise ValueError(f"Error loading CSV: {e}")
    print(f"Loaded dataset with {data.shape[0]} rows and {data.shape[1]} columns.")
    return data


def summarize_data(data):
    summary = data.describe(include="all").T
    missing_values = data.isnull().sum()
    return summary, missing_values

def visualize_correlation(data):
    numeric_data = data.select_dtypes(include=["number"])
    if numeric_data.empty:
        print("No numeric data to visualize.")
        return None
    correlation = numeric_data.corr()
    plt.figure(figsize=(6, 6))
    sns.heatmap(correlation, annot=True, cmap="coolwarm")
    plt.title("Correlation Matrix")
    file_name = "correlation_matrix.png"
    plt.savefig(file_name)
    plt.clf()
    print(f"Correlation matrix saved as {file_name}.")
    return file_name

def create_readme(summary, missing, insights, chart_files):
    with open("README.md", "w") as file:
        file.write("# Automated Analysis Report\n\n")
        file.write("## Summary\n\n")
        file.write(summary.to_string() + "\n\n")
        file.write("## Missing Values\n\n")
        file.write(missing.to_string() + "\n\n")
        file.write("## Insights from GPT-4o-Mini\n\n")
        file.write(insights + "\n\n")
        file.write("## Visualizations\n\n")
        for chart in chart_files:
            file.write(f"![{chart}]({chart})\n")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Automated Analysis Tool")
    parser.add_argument("csv_file", help="Input CSV file for analysis")
    args = parser.parse_args()

    # Load dataset
    data = load_csv(args.csv_file)

    # Summarize data
    summary, missing = summarize_data(data)

    # Generate a correlation matrix visualization
    chart_files = []
    correlation_chart = visualize_correlation(data)
    if correlation_chart:
        chart_files.append(correlation_chart)

    # Ask GPT for insights
    prompt = f"""
    I have analyzed a dataset with the following summary:\n{summary}\n
    Missing values:\n{missing}\n
    Please provide insights and suggestions for further analysis.
    """
    insights = ask_gpt(prompt)

    # Create README.md
    create_readme(summary, missing, insights, chart_files)
    print("Analysis completed. Results saved to README.md.")

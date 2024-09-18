from flask import Flask, render_template, jsonify
import requests
import base64
import datetime
import json
import pandas as pd
import plotly.graph_objects as go

app = Flask(__name__)

import json

with open('/home/harsh/julius-harshit-projects/analytics_dashboard/config.json') as config_file:
    config = json.load(config_file)

username = config.get('username')
secret = config.get('secret')

if not username or not secret:
    raise ValueError("Username or Secret not found in config.json!")

# Your Mixpanel project ID
project_id = '2465524'

# Encode the credentials for Basic Auth
auth_string = base64.b64encode(f'{username}:{secret}'.encode('utf-8')).decode('utf-8')

def get_mixpanel_data():
    # Define the date range
    end_date = datetime.datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')

    # JQL query to get "clicks" and "hovers" within the date range
    jql_query = f"""
    function main() {{
        return Events({{
            from_date: '{start_date}',
            to_date: '{end_date}'
        }})
        .filter(function(event) {{
            return (event.name == "Job Clicked" || event.name == "Job Click" || event.name == "Job Hover") &&
                   event.properties["$current_url"].includes("dcdoee.careerpathplatform.com");
        }})
        .groupBy(["name", "properties.Job Title"], mixpanel.reducer.count());
    }}
    """

    # Convert the JQL script to JSON format
    data = json.dumps({'script': jql_query})

    # Send the JQL query to Mixpanel with the project_id as a parameter
    response = requests.post(
        f'https://mixpanel.com/api/2.0/jql?project_id={project_id}',
        headers={
            'Authorization': f'Basic {auth_string}',
            'Content-Type': 'application/json',
        },
        data=data
    )

    if response.status_code == 200:
        return response.json()
    else:
        return None

def prepare_pie_chart_data(df, top_n=15):
    # Sort the DataFrame by count in descending order
    df_sorted = df.sort_values(by='Count', ascending=False)

    # Take the top N jobs
    top_jobs = df_sorted.head(top_n)

    # Sum the remaining jobs into "Other"
    other_sum = df_sorted.iloc[top_n:]['Count'].sum()

    # Add "Other" to the DataFrame
    if other_sum > 0:
        other_row = pd.DataFrame({"Job Title": ["Other"], "Count": [other_sum]})
        final_df = pd.concat([top_jobs, other_row], ignore_index=True)
    else:
        final_df = top_jobs

    return final_df

@app.route('/')
def index():
    results = get_mixpanel_data()
    if not results:
        return "No data available from Mixpanel."

    # Separate clicks and hovers into two lists
    clicks_data = []
    hovers_data = []

    for event in results:
        if event['key'][0] in ["Job Clicked", "Job Click"]:
            clicks_data.append([event['key'][1], event['value']])
        elif event['key'][0] == "Job Hover":
            hovers_data.append([event['key'][1], event['value']])

    # Convert lists to DataFrames
    clicks_df = pd.DataFrame(clicks_data, columns=["Job Title", "Count"])
    hovers_df = pd.DataFrame(hovers_data, columns=["Job Title", "Count"])

    # Prepare pie chart data for clicks and hovers
    clicks_pie_data = prepare_pie_chart_data(clicks_df, top_n=15)
    hovers_pie_data = prepare_pie_chart_data(hovers_df, top_n=15)

    # Create pie chart for job clicks
    fig_clicks_pie = go.Figure(
        data=[go.Pie(labels=clicks_pie_data['Job Title'], values=clicks_pie_data['Count'], hole=0.3)]
    )
    fig_clicks_pie.update_layout(
        title="Roles generating deeper interest (Top 15 + Other Clicks)",
        height=670,  # Adjust height for more space
        legend=dict(
            orientation="h",  # Horizontal legend
            yanchor="bottom",
            y=-0.4,  # Move legend below the plot
            xanchor="center",
            x=0.5,
            font=dict(size=10)  # font for legend
        )
    )
    clicks_plot_html = fig_clicks_pie.to_html(full_html=False)

    # Create pie chart for job hovers
    fig_hovers_pie = go.Figure(
        data=[go.Pie(labels=hovers_pie_data['Job Title'], values=hovers_pie_data['Count'], hole=0.3)]
    )
    fig_hovers_pie.update_layout(
        title="Roles generating initial interest (Top 15 + Other Hovers)",
        height=660,  # Adjust height for more space
        legend=dict(
            orientation="h",  # Horizontal legend
            yanchor="bottom",
            y=-0.4,  # Move legend below the plot
            xanchor="center",
            x=0.5,
            font=dict(size=10)  # font for legend
        )
    )
    hovers_plot_html = fig_hovers_pie.to_html(full_html=False)

    return render_template('index.html', clicks_plot=clicks_plot_html, hovers_plot=hovers_plot_html)

if __name__ == '__main__':
    app.run(debug=True)
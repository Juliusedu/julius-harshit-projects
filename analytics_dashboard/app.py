import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import plotly.graph_objects as go
from io import BytesIO
from flask import Flask, make_response, render_template, request
from google.oauth2 import service_account
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest

app = Flask(__name__)


KEY_FILE_LOCATION = '/home/harsh/julius-harshit-projects/analytics_dashboard/development.json'
SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
# PROPERTY_ID = '414149946'  # Replace with your GA4 property ID

credentials = service_account.Credentials.from_service_account_file(
    KEY_FILE_LOCATION, scopes=SCOPES)

client = BetaAnalyticsDataClient(credentials=credentials)

def calculate_date(date_str):
    if date_str == 'today':
        return datetime.today()
    elif date_str == 'yesterday':
        return datetime.today() - timedelta(days=1)
    elif 'daysAgo' in date_str:
        days_ago = int(date_str.replace('daysAgo', ''))
        return datetime.today() - timedelta(days=days_ago)
    else:
        return datetime.strptime(date_str, '%Y-%m-%d')

def get_report(client, metrics, dimensions, start_date, end_date, property_id):
    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[{"start_date": start_date, "end_date": end_date}],
        dimensions=[{"name": dim} for dim in dimensions],
        metrics=[{"name": met} for met in metrics]
    )
    response = client.run_report(request)
    return response

def parse_response(response, dimensions, metrics):
    rows = []
    for row in response.rows:
        row_data = [row.dimension_values[i].value for i in range(len(dimensions))] + \
                   [row.metric_values[i].value for i in range(len(metrics))]
        rows.append(row_data)
    columns = dimensions + metrics
    df = pd.DataFrame(rows, columns=columns)
    return df

def plot_graph(df, x_column, y_column, title, xlabel, ylabel, date_range):
    # Convert average session duration from seconds to minutes if necessary
    if y_column == "averageSessionDuration":
        df[y_column] = df[y_column] / 60
        ylabel = "Avg Session Duration (mins)"

    # Aggregate data by date
    df_agg = df.groupby(x_column).sum().reset_index()

    fig = px.line(df_agg, x=x_column, y=y_column, title=title, labels={x_column: xlabel, y_column: ylabel})

    # Determine the duration of the date range
    start_date = pd.to_datetime(df[x_column].min())
    end_date = pd.to_datetime(df[x_column].max())
    duration = (end_date - start_date).days

    # Adjust x-axis formatting based on the date range duration
    if duration <= 30:
        fig.update_xaxes(dtick="D1", tickformat="%Y-%m-%d")
    elif duration <= 60:
        tickvals = pd.date_range(start=start_date, end=end_date, freq='2D').to_list()
        fig.update_xaxes(tickmode='array', tickvals=tickvals, tickformat="%Y-%m-%d")
    elif duration <= 90:
        tickvals = pd.date_range(start=start_date, end=end_date, freq='W').to_list()
        fig.update_xaxes(tickmode='array', tickvals=tickvals, tickformat="%Y-%m-%d")
    elif duration <= 180:
        tickvals = pd.date_range(start=start_date, end=end_date, freq='15D').to_list()
        fig.update_xaxes(tickmode='array', tickvals=tickvals, tickformat="%Y-%m-%d")
    else:
        tickvals = pd.date_range(start=start_date, end=end_date, freq='M').to_list()
        fig.update_xaxes(tickmode='array', tickvals=tickvals, tickformat="%Y-%m")

    graph_html = fig.to_html(full_html=False)
    return graph_html

def plot_event_count_by_name_over_time(df):
    fig = px.bar(
        df,
        x='date',
        y='eventCount',
        color='eventName',
        title='Event Count by Event Name Over Time',
        labels={'date': 'Date', 'eventCount': 'Event Count', 'eventName': 'Event Name'}
    )
    # Determine the duration of the date range
    start_date = pd.to_datetime(df['date'].min())
    end_date = pd.to_datetime(df['date'].max())
    duration = (end_date - start_date).days
    # Adjust x-axis formatting based on the date range duration
    if duration <= 30:
        fig.update_xaxes(dtick="D1", tickformat="%Y-%m-%d")
    elif duration <= 60:
        tickvals = pd.date_range(start=start_date, end=end_date, freq='2D').to_list()
        fig.update_xaxes(tickmode='array', tickvals=tickvals, tickformat="%Y-%m-%d")
    elif duration <= 90:
        tickvals = pd.date_range(start=start_date, end=end_date, freq='W').to_list()
        fig.update_xaxes(tickmode='array', tickvals=tickvals, tickformat="%Y-%m-%d")
    elif duration <= 180:
        tickvals = pd.date_range(start=start_date, end=end_date, freq='15D').to_list()
        fig.update_xaxes(tickmode='array', tickvals=tickvals, tickformat="%Y-%m-%d")
    else:
        tickvals = pd.date_range(start=start_date, end=end_date, freq='M').to_list()
        fig.update_xaxes(tickmode='array', tickvals=tickvals, tickformat="%Y-%m")

    graph_html = fig.to_html(full_html=False)
    return graph_html



def bar_graph(df, x_column, y_column, title, xlabel, ylabel, top_n=None, rotation=90, x_font_size=10):
    location_df = df.groupby(x_column)[y_column].sum().reset_index()
    location_df = location_df.sort_values(by=y_column, ascending=False)
    
    if top_n:
        location_df = location_df.head(top_n)

    fig = px.bar(location_df, x=x_column, y=y_column, title=title, labels={x_column: xlabel, y_column: ylabel})
    fig.update_layout(xaxis_tickangle=rotation,xaxis=dict(tickfont=dict(size=x_font_size))
)

    graph_html = fig.to_html(full_html=False)
    return graph_html


def pie_chart(df, column, title):
    fig = px.pie(df, names=column, title=title, hole=0.3, 
                 labels={column: column}, 
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    
    # Customize hover information to show percentages
    fig.update_traces(textinfo='percent+label', insidetextorientation='radial')

    graph_html = fig.to_html(full_html=False)
    return graph_html


def plot_usa_map(df, state_column, value_column):
    # Ensure state abbreviations are in uppercase
    df[state_column] = df[state_column].str.upper()

    # Aggregate the data by state
    aggregated_df = df.groupby(state_column)[value_column].sum().reset_index()

    # Ensure all values are numeric
    aggregated_df[value_column] = pd.to_numeric(aggregated_df[value_column], errors='coerce')

    # Ensure that the color scale maps correctly to the data range
    min_value = aggregated_df[value_column].min()
    max_value = aggregated_df[value_column].max()

    # Generate the USA map using Plotly
    fig = px.choropleth(
        aggregated_df,
        locations=state_column,
        locationmode='USA-states',
        color=value_column,
        hover_name=state_column,
        color_continuous_scale=px.colors.sequential.Viridis,  # Choose color scale
        title='Active Users by Region'
    )

    # Update the layout to reflect a numerical color axis scale
    fig.update_layout(
        geo_scope='usa',
        coloraxis_colorbar=dict(
            title="Active Users",
            tickvals=[min_value, (min_value + max_value) / 2, max_value],  # Choose desired number of ticks
            ticktext=[f"{min_value:.0f}", f"{(min_value + max_value) / 2:.0f}", f"{max_value:.0f}"],  # Numeric tick labels
            lenmode="fraction",  # Set length of color bar
        )
    )
    graph_html = fig.to_html(full_html=False)
    return graph_html

@app.route('/', methods=['GET', 'POST'])
def dashboard():
    # Default property ID if none is provided
    property_id = request.args.get('property_id', '414149946')

    # Dictionary mapping property IDs to titles
    property_titles = {
    '383822713': 'Julius - Webflow GA4',
    '314080261': 'Julius Live',
    '405124596': 'TWT',
    '404949071': 'Network',
    '448075572': 'NENY',
    '405046512': 'My',
    '405050777': 'MN',
    '405024738': 'KFC2',
    '405113132': 'KFC',
    '414142783': 'Electrical Construction',
    '414149946': 'DCDOEE',
    '405096830': 'AESP',
    '405060547': 'Advanced Manufacturing'
    }

    # Get the title from the property ID, or a default title if not found
    title = property_titles.get(property_id, 'Analytics Dashboard')

    date_range = request.args.get('date_range', '30daysAgo-today')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    predefined_ranges = {
        'today': ('today', 'today'),'yesterday': ('yesterday', 'yesterday'),
        'this_week': ('7daysAgo', 'today'),'last_week': ('14daysAgo', '7daysAgo'),
        '7daysAgo-today': ('7daysAgo', 'today'),'14daysAgo-today': ('14daysAgo', 'today'),
        '28daysAgo-today': ('28daysAgo', 'today'),'30daysAgo-today': ('30daysAgo', 'today'),
        '60daysAgo-today': ('60daysAgo', 'today'),'90daysAgo-today': ('90daysAgo', 'today'),'last_12months': ('365daysAgo', 'today'),
    }

    if date_range == 'custom':
        if not start_date or not end_date:
            start_date, end_date = '30daysAgo', 'today'  # Default to past 30 days
    else:
        start_date, end_date = predefined_ranges.get(date_range, ('30daysAgo', 'today'))

    metrics = [
        "activeUsers","newUsers","screenPageViews","sessions","averageSessionDuration","bounceRate","eventCount"
    ]

    dimensions = [
        "date","country","city","region","deviceCategory","browser","pageTitle","sessionDefaultChannelGroup","eventName"
    ]

    try:
        response = get_report(client, metrics, dimensions, start_date, end_date, property_id)
        df = parse_response(response, dimensions, metrics)

        # Ensure all metric columns are numeric
        for metric in metrics:
            if metric in df.columns:
                df[metric] = pd.to_numeric(df[metric], errors='coerce')

        # Convert date to datetime format
        df['date'] = pd.to_datetime(df['date'])
        state_abbreviations = {
            'Alabama': 'AL','Alaska': 'AK','Arizona': 'AZ','Arkansas': 'AR','California': 'CA',
            'Colorado': 'CO','Connecticut': 'CT','Delaware': 'DE','Florida': 'FL','Georgia': 'GA','Hawaii': 'HI','Idaho': 'ID',
            'Illinois': 'IL','Indiana': 'IN','Iowa': 'IA','Kansas': 'KS','Kentucky': 'KY','Louisiana': 'LA','Maine': 'ME',
            'Maryland': 'MD','Massachusetts': 'MA','Michigan': 'MI','Minnesota': 'MN','Mississippi': 'MS','Missouri': 'MO',
            'Montana': 'MT','Nebraska': 'NE','Nevada': 'NV','New Hampshire': 'NH','New Jersey': 'NJ','New Mexico': 'NM',
            'New York': 'NY','North Carolina': 'NC','North Dakota': 'ND','Ohio': 'OH','Oklahoma': 'OK','Oregon': 'OR',
            'Pennsylvania': 'PA','Rhode Island': 'RI','South Carolina': 'SC','South Dakota': 'SD','Tennessee': 'TN','Texas': 'TX',
            'Utah': 'UT','Vermont': 'VT','Virginia': 'VA','Washington': 'WA','West Virginia': 'WV','Wisconsin': 'WI','Wyoming': 'WY'
        }
        # Map full state names to abbreviations if necessary
        df['region'] = df['region'].map(state_abbreviations).fillna(df['region'])

        graphs = {}
        # Calculate the date range duration in days
        start_date_obj = calculate_date(start_date)
        end_date_obj = calculate_date(end_date)
        date_range_duration = (end_date_obj - start_date_obj).days

        # Generate plots and add them to the dictionary
        graphs['active_users'] = plot_graph(df, 'date', 'activeUsers', 'Active Users Over Time', 'Date', 'Active Users', date_range_duration)
        graphs['new_users'] = plot_graph(df, 'date', 'newUsers', 'New Users Over Time', 'Date', 'New Users', date_range_duration)
        graphs['page_views'] = plot_graph(df, 'date', 'screenPageViews', 'Page Views Over Time', 'Date', 'Page Views', date_range_duration)
        graphs['sessions'] = plot_graph(df, 'date', 'sessions', 'Sessions Over Time', 'Date', 'Sessions', date_range_duration)
        graphs['avg_session_duration'] = plot_graph(df, 'date', 'averageSessionDuration', 'Average Session Duration Over Time', 'Date', 'Average Session Duration', date_range_duration)
        graphs['event_count'] = plot_graph(df, 'date', 'eventCount', 'Event Count Over Time', 'Date', 'Event Count', date_range_duration)
        graphs['event_count_by_name_over_time'] = plot_event_count_by_name_over_time(df)
        graphs['sessions_by_channel_group'] = bar_graph(df, 'sessionDefaultChannelGroup', 'sessions', 'Sessions by Channel Group', 'Channel Group', 'Sessions', rotation=90)
        graphs['bounce_rate'] = plot_graph(df, 'date', 'bounceRate', 'Bounce Rate Over Time', 'Date', 'Bounce Rate', date_range_duration)
        graphs['active_users_by_country'] = bar_graph(df, 'country', 'activeUsers', 'Active Users by Country', 'Country', 'Active Users', rotation=90)
        graphs['active_users_by_city'] = bar_graph(df, 'city', 'activeUsers', 'Active Users by City', 'City', 'Active Users', top_n=50, rotation=90)
        graphs['active_users_by_device'] = pie_chart(df, 'deviceCategory', 'Active Users by Device Category')
        graphs['active_users_by_browser'] = pie_chart(df, 'browser', 'Active Users by Browser')
        graphs['active_users_by_pageTitle'] = bar_graph(df, 'pageTitle', 'activeUsers', 'Active Users by Page Title', 'Page Title', 'Active Users', top_n=5, rotation=10, x_font_size=8)
        graphs['map_active_users_by_region'] = plot_usa_map(df, 'region', 'activeUsers')
        
        return render_template('dashboard.html',title=title, graphs=graphs, property_id = property_id,date_range=date_range, start_date=start_date, end_date=end_date)

    except Exception as e:
        return f"An error occurred: {e}"

if __name__ == '__main__':
    app.run(debug=True)


# def plot_usa_map(df, state_column, value_column):
#     # Ensure state abbreviations are in uppercase
#     df[state_column] = df[state_column].str.upper()

#     # Aggregate the data by state
#     aggregated_df = df.groupby(state_column)[value_column].sum().reset_index()

#     # Ensure all values are numeric
#     aggregated_df[value_column] = pd.to_numeric(aggregated_df[value_column], errors='coerce')

#     # Ensure that the color scale maps correctly to the data range
#     min_value = aggregated_df[value_column].min()
#     max_value = aggregated_df[value_column].max()

#     fig = px.choropleth(
#         aggregated_df,
#         locations=state_column,
#         locationmode='USA-states',
#         color=value_column,
#         hover_name=state_column,
#         color_continuous_scale=px.colors.sequential.Viridis,  # Ensure appropriate scale is used
#         title='Active Users by Region'
#     )

#     fig.update_layout(
#         geo_scope='usa',  # Focus on the USA
#         coloraxis_colorbar=dict(
#             title="Active Users",
#             tickvals=[min_value, max_value],
#             ticktext=['Low', 'High']
#         )
#     )

#     graph_html = fig.to_html(full_html=False)
#     return graph_html


# import pandas as pd
# import matplotlib
# matplotlib.use('Agg')
# import matplotlib.pyplot as plt
# from io import BytesIO
# import base64
# from flask import Flask, render_template, request
# from google.oauth2 import service_account
# from google.analytics.data_v1beta import BetaAnalyticsDataClient
# from google.analytics.data_v1beta.types import RunReportRequest
# import matplotlib.dates as mdates

# # from datetime import datetime

# app = Flask(__name__)

# # JSON secret key file 
# KEY_FILE_LOCATION = 'development.json'  # Ensure this path is correct
# SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']

# # Authenticate and construct the service
# credentials = service_account.Credentials.from_service_account_file(
#     KEY_FILE_LOCATION, scopes=SCOPES)

# client = BetaAnalyticsDataClient(credentials=credentials)

# def get_report(client, metrics, dimensions, start_date, end_date):
#     request = RunReportRequest(
#         property=f"properties/{PROPERTY_ID}",
#         date_ranges=[{"start_date": start_date, "end_date": end_date}],
#         dimensions=[{"name": dim} for dim in dimensions],
#         metrics=[{"name": met} for met in metrics]
#     )
#     response = client.run_report(request)
#     return response

# def parse_response(response, dimensions, metrics):
#     rows = []
#     for row in response.rows:
#         row_data = [row.dimension_values[i].value for i in range(len(dimensions))] + \
#                    [row.metric_values[i].value for i in range(len(metrics))]
#         rows.append(row_data)
#     columns = dimensions + metrics
#     df = pd.DataFrame(rows, columns=columns)
#     return df


# def plot_graph(df, x_column, y_column, title, xlabel, ylabel, date_range):
#     # Convert average session duration from seconds to minutes if necessary
#     if y_column == "averageSessionDuration":
#         df[y_column] = df[y_column] / 60
#         ylabel = "Avg Session Duration (mins)"  # Update y-axis label to indicate minutes

#     # Aggregate data by date
#     df_agg = df.groupby(x_column).sum().reset_index()

#     fig = px.line(df_agg, x=x_column, y=y_column, title=title, labels={x_column: xlabel, y_column: ylabel})

#     # Determine the duration of the date range
#     start_date = pd.to_datetime(df[x_column].min())
#     end_date = pd.to_datetime(df[x_column].max())
#     duration = (end_date - start_date).days

#     # Adjust x-axis formatting based on the date range duration
#     if duration <= 30:
#         fig.update_xaxes(dtick="D1", tickformat="%Y-%m-%d")
#     elif duration <= 60:
#         tickvals = pd.date_range(start=start_date, end=end_date, freq='2D').to_list()
#         fig.update_xaxes(tickmode='array', tickvals=tickvals, tickformat="%Y-%m-%d")
#     elif duration <= 90:
#         tickvals = pd.date_range(start=start_date, end=end_date, freq='W').to_list()
#         fig.update_xaxes(tickmode='array', tickvals=tickvals, tickformat="%Y-%m-%d")
#     elif duration <= 180:
#         tickvals = pd.date_range(start=start_date, end=end_date, freq='15D').to_list()
#         fig.update_xaxes(tickmode='array', tickvals=tickvals, tickformat="%Y-%m-%d")
#     else:
#         tickvals = pd.date_range(start=start_date, end=end_date, freq='M').to_list()
#         fig.update_xaxes(tickmode='array', tickvals=tickvals, tickformat="%Y-%m")

#     graph_html = fig.to_html(full_html=False)
#     return graph_html

# def plot_graph(df, x_column, y_column, title, xlabel, ylabel):
#     # Aggregate data by date
#     df_agg = df.groupby(x_column).sum().reset_index()

#     plt.figure(figsize=(16, 10))
#     plt.plot(df_agg[x_column], df_agg[y_column], linestyle="-", marker='o', color='b')
#     plt.xticks(rotation=90)
#     plt.title(title)
#     plt.xlabel(xlabel)
#     plt.ylabel(ylabel)
#     plt.grid(True)

#     # Determine the date range
#     date_range = (df_agg[x_column].max() - df_agg[x_column].min()).days

#     # Set date format for x-axis
#     ax = plt.gca()

#     if date_range <= 30:
#         ax.xaxis.set_major_locator(mdates.DayLocator())
#         ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
#     elif date_range <= 90:
#         ax.xaxis.set_major_locator(mdates.WeekdayLocator())
#         ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
#     elif date_range <= 180:
#         ax.xaxis.set_major_locator(mdates.DayLocator(interval=15))
#         ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
#     else:
#         ax.xaxis.set_major_locator(mdates.MonthLocator())
#         ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

#     plt.gcf().autofmt_xdate()

#     img = BytesIO()
#     plt.savefig(img, format='png')
#     img.seek(0)
#     graph_url = base64.b64encode(img.getvalue()).decode('utf8')
#     plt.close()
#     return graph_url

# def bar_graph(df, x_column, y_column, title, xlabel, ylabel, top_n=None, rotation=90):
#     location_df = df.groupby(x_column)[y_column].sum().reset_index()
#     location_df = location_df.sort_values(by=y_column, ascending=False)
    
#     if top_n:
#         location_df = location_df.head(top_n)

#     plt.figure(figsize=(16, 11))
#     plt.bar(location_df[x_column], location_df[y_column], color='b')
#     plt.xticks(rotation=rotation)
#     plt.title(title)
#     plt.xlabel(xlabel)
#     plt.ylabel(ylabel)
#     plt.grid(True)
    
#     img = BytesIO()
#     plt.savefig(img, format='png')
#     img.seek(0)
#     graph_url = base64.b64encode(img.getvalue()).decode('utf8')
#     plt.close()
#     return graph_url

# def pie_chart(df, column, title):
#     plt.figure(figsize=(16, 10))
#     df[column].value_counts().plot.pie(autopct='%1.1f%%', startangle=140, cmap='tab20', fontsize=12)
#     plt.title(title)
#     plt.ylabel('')  # Hide y-label
#     plt.grid(True)
    
#     img = BytesIO()
#     plt.savefig(img, format='png')
#     img.seek(0)
#     graph_url = base64.b64encode(img.getvalue()).decode('utf8')
#     plt.close()
#     return graph_url


# @app.route('/')
# def dashboard():
#     date_range = request.args.get('date_range', '30daysAgo-today')
#     start_date = request.args.get('start_date')
#     end_date = request.args.get('end_date')

#     # Map the custom date ranges to the appropriate Google Analytics date range formats
#     predefined_ranges = {
#         'today': ('today', 'today'),
#         # 'yesterday': ('yesterday', 'yesterday'),
#         'this_week': ('7daysAgo', 'today'),
#         'last_week': ('14daysAgo', '7daysAgo'),
#         '7daysAgo-today': ('7daysAgo', 'today'),
#         '14daysAgo-today': ('14daysAgo', 'today'),
#         '28daysAgo-today': ('28daysAgo', 'today'),
#         '30daysAgo-today': ('30daysAgo', 'today'),
#         '60daysAgo-today': ('60daysAgo', 'today'),
#         '90daysAgo-today': ('90daysAgo', 'today'),
#         # 'quarter_to_date': ('3monthsAgo', 'today'), 
#         'last_12months': ('365daysAgo', 'today'),
#         # 'year_to_date': ('2024-01-01', 'today')  # Adjust to the start of the year
#     }

#     if date_range == 'custom':
#         if not start_date or not end_date:
#             start_date, end_date = '30daysAgo', 'today'  # Default to past 30 days
#     else:
#         start_date, end_date = predefined_ranges.get(date_range, ('30daysAgo', 'today'))

#     metrics = [
#         "activeUsers",
#         "newUsers",
#         "screenPageViews",
#         "sessions",
#         "averageSessionDuration",
#         "bounceRate",
#         "eventCount"
#     ]

#     dimensions = [
#         "date",
#         "country",
#         "city",
#         "deviceCategory",
#         "browser",
#         "pageTitle",
#         "sessionDefaultChannelGroup"
#     ]

#     try:
#         response = get_report(client, metrics, dimensions, start_date, end_date)
#         df = parse_response(response, dimensions, metrics)

#         # Ensure all metric columns are numeric
#         for metric in metrics:
#             if metric in df.columns:
#                 df[metric] = pd.to_numeric(df[metric], errors='coerce')

#         # Convert date to datetime format
#         df['date'] = pd.to_datetime(df['date'])

#         graphs = {}

#         # Generate plots and add them to the dictionary
#         graphs['active_users'] = plot_graph(df, 'date', 'activeUsers', 'Active Users Over Time', 'Date', 'Active Users')
#         graphs['new_users'] = plot_graph(df, 'date', 'newUsers', 'New Users Over Time', 'Date', 'New Users')
#         graphs['page_views'] = plot_graph(df, 'date', 'screenPageViews', 'Page Views Over Time', 'Date', 'Page Views')
#         graphs['sessions'] = plot_graph(df, 'date', 'sessions', 'Sessions Over Time', 'Date', 'Sessions')
#         graphs['avg_session_duration'] = plot_graph(df, 'date', 'averageSessionDuration', 'Average Session Duration Over Time', 'Date', 'Avg Session Duration')
#         graphs['event_count'] = plot_graph(df, 'date', 'eventCount', 'Event Count Over Time', 'Date', 'Event Count')
#         graphs['sessions_by_channel_group'] = bar_graph(df, 'sessionDefaultChannelGroup', 'sessions', 'Sessions by Channel Group', 'Channel Group', 'Sessions')
#         graphs['bounce_rate'] = plot_graph(df, 'date', 'bounceRate', 'Bounce Rate Over Time', 'Date', 'Bounce Rate')
#         graphs['active_users_by_country'] = bar_graph(df, 'country', 'activeUsers', 'Active Users by Country', 'Country', 'Active Users')
#         graphs['active_users_by_city'] = bar_graph(df, 'city', 'activeUsers', 'Active Users by City', 'City', 'Active Users', top_n=40)
#         graphs['active_users_by_device'] = pie_chart(df, 'deviceCategory', 'Active Users by Device Category')
#         graphs['active_users_by_browser'] = pie_chart(df, 'browser', 'Active Users by Browser')
#         graphs['active_users_by_pageTitle'] = bar_graph(df, 'pageTitle', 'activeUsers', 'Active Users by Page Title', 'Page Title', 'Active Users', top_n=5, rotation=8)

#         return render_template('dashboard.html', graphs=graphs, date_range=date_range)

#     except Exception as e:
#         print(f"An error occurred: {e}")
#         return f"An error occurred: {e}"

# if __name__ == '__main__':
#     app.run(debug=True)
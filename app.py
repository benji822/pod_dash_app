# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import os
import re
from glob import glob

import dash
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dash_table, dcc, html
from dash.dependencies import Input, Output
from plotly.subplots import make_subplots

app = dash.Dash(__name__)
server = app.server

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
output_files_name = [y for x in os.walk('./data/output') for y in glob(os.path.join(x[0], '*.xlsx'))]
downtime_files_name = [y for x in os.walk('./data/downtime') for y in glob(os.path.join(x[0], '*.xlsx'))]

output_lines_name = [re.search('L.{1}', name).group(0) for name in output_files_name]
downtime_lines_name = [re.search('L.{1}', name).group(0) for name in downtime_files_name]

# Get output data from excel file
output_df = {}
for x in output_files_name:
    arr = []
    for y in range(10):
        arr.append(pd.read_excel(x, sheet_name=y, parse_dates=["Createtime"], index_col="Createtime"))
    line_name = re.search('L.{1}', x).group(0)
    output_df[line_name] = arr


# Get downtime data from excel file
downtime_df = {}
for x in downtime_files_name:
    xl = pd.ExcelFile(x)
    res = len(xl.sheet_names)
    arr = []
    for y in range(res):
        arr.append(pd.read_excel(x, sheet_name=y))
    downtime_line_name = re.search('L.{1}', x).group(0)
    downtime_df[downtime_line_name] = arr


# Format the downtime data for plot
downtime_date_dict = {}
for l in downtime_lines_name:
    temp = {}
    downtime_df_copy = downtime_df[l].copy()
    line_date_arr = [x.loc[0]["Createtime"] for x in downtime_df_copy[::3]]
    for d in line_date_arr:
        sub_temp = {}
        for v in range(3):
            temp_df = downtime_df_copy.pop(0)
            temp_df = temp_df.fillna(0)
            if 'Createtime' in temp_df.keys():
                temp_df.set_index('Createtime', inplace=True)
                temp_df["Total_minutes"] = np.round(temp_df["Total_seconds"] /60, 0)
                sub_temp["hourly_downtime"] = temp_df
                
            elif 'WORKCELL_STATUS' in temp_df.keys():
                temp_df.set_index('WORKCELL_STATUS', inplace=True)
                sub_temp["downtime_breakdown"] = temp_df

            else:
                sub_temp["downtime"] = temp_df
        temp[d.strftime("%m/%d/%Y")] = sub_temp
    downtime_date_dict[l] = temp


date_arr = list(set([x.date() for x in output_df[output_lines_name[0]][0].index]))
date_arr.sort()
date_str_arr = [d.strftime("%m/%d/%Y")  for d in date_arr]


# Setup default data for figure
default_output_df = output_df[output_lines_name[0]][0].loc[date_str_arr[0]]
default_downtime_df = downtime_date_dict[downtime_lines_name[0]][date_str_arr[0]]['downtime']
default_downtime_breakdown_df = downtime_date_dict[downtime_lines_name[0]][date_str_arr[0]]['downtime_breakdown']['wc1']
default_hourly_downtime_df = downtime_date_dict[downtime_lines_name[0]][date_str_arr[0]]["hourly_downtime"][downtime_date_dict[downtime_lines_name[0]][date_str_arr[0]]["hourly_downtime"]['WORKCELL'] == 1]
default_breakdown_pie_df = pd.DataFrame(default_downtime_breakdown_df)
default_breakdown_pie_df['wc1'] = pd.to_timedelta(default_breakdown_pie_df["wc1"])
default_breakdown_pie_df["total_seconds"] = default_breakdown_pie_df["wc1"].dt.total_seconds()


# Create figure for the data
# output_fig = px.bar(default_output_df, y="HourlyOutput", text='HourlyOutput')
# downtime_fig = px.line(default_hourly_downtime_df, x=default_hourly_downtime_df.index, y='Total_minutes')
downtime_fig_pie = px.pie(default_breakdown_pie_df, values='total_seconds', names=default_breakdown_pie_df.index)

make_float = lambda x: "{:,.2f}%".format(x*100)

output_data_table_df = output_df[output_lines_name[0]][0].loc[date_str_arr[0]].copy()
output_data_table_df.reset_index(inplace=True)
output_data_table_df['NGRate'] = output_data_table_df['NGRate'].apply(make_float)
output_data_table_df['Yield'] = output_data_table_df['Yield'].apply(make_float)
output_data_table_df['YieldWithoutSample'] = output_data_table_df['YieldWithoutSample'].apply(make_float)
output_data_table_df = output_data_table_df.rename(columns = {'index':'new column name'})

downtime_data_table_df = default_breakdown_pie_df.copy()
downtime_data_table_df = default_breakdown_pie_df.rename({'wc1': 'total_time'}, axis=1)
downtime_data_table_df['total_time'] = downtime_data_table_df['total_time'].astype(str)
downtime_data_table_df.reset_index(inplace=True)
downtime_data_table_df = downtime_data_table_df.rename(columns = {'index':'new column name'})


# Create figure with output and downtime
mul_fig = make_subplots(specs=[[{"secondary_y": True}]])
# Add traces
mul_fig.add_trace(
    go.Bar(x=default_output_df.index, y=default_output_df["HourlyOutput"], name="Hourly output"),
    secondary_y=False,
)

mul_fig.add_trace(
    go.Scatter(x=default_hourly_downtime_df.index, y=default_hourly_downtime_df['Total_minutes'], name="Downtime in minutes"),
    secondary_y=True,
)

# Add mul_figure title
mul_fig.update_layout(
    title_text="Hourly output and downtime in minutes"
)

# Set x-axis title
mul_fig.update_xaxes(title_text="Createtime")

# Set y-axes titles
mul_fig.update_yaxes(title_text="<b>Output</b>", secondary_y=False)
mul_fig.update_yaxes(title_text="<b>Downtime</b> in minutes", secondary_y=True)


app.layout = html.Div(children=[
    html.H1(
        children='POD Automation Line Data Analysis',
        style={
        'textAlign': 'center',
        'color': colors['text']
    }),

    html.Div(
        children=[
            html.Div(
                children=[
                    html.Label('Date'),
                    dcc.Dropdown(
                        id="data_date",
                        options=[{"label": f"{i}", "value": i} for i in date_str_arr],
                        value=date_str_arr[0],
                        style={"marginTop": '10px'}
                    )
                ],
                style={"width": '100%', "padding": '10px'}
            ),

            html.Div(
                children=[
                    html.Label('Line Number'),
                    dcc.Dropdown(
                        id="data_line",
                        options=[{"label": i, "value": i} for i in output_lines_name],
                        value=output_lines_name[0],
                        style={"marginTop": '10px'}
                    )
                ],
                style={"width": '100%', "padding": '10px'}
            ),

            html.Div(
                children=[
                    html.Label('Workcell Number'),
                    dcc.Dropdown(
                        id="data_workcell",
                        options=[{"label": f"Workcell {i + 1}", "value": i} for i in range(10)],
                        value=0,
                        style={"marginTop": '10px'}
                    )
                ],
                style={"width": '100%', "padding": '10px'}
            ),
        ],
        style={'display': 'flex', 'justifyContent': 'space-between'}
    ),

    dcc.Graph(id="output_downtime_graph", figure=mul_fig),

    html.H2(
        children='Table Details',
        style={
        'textAlign': 'center',
        'color': colors['text']
    }),

    dash_table.DataTable(
        id='data_table',
        columns=[{"name": i, "id": i} for i in output_data_table_df.columns],
        data=output_data_table_df.to_dict('records'),
    ),

    html.H2(
        children='Downtime',
        style={
        'textAlign': 'center',
        'color': colors['text']
    }),
    
    dash_table.DataTable(
        id='downtime_table',
        columns=[{"name": i, "id": i} for i in downtime_data_table_df.columns],
        data=downtime_data_table_df.to_dict('records'),
    ),

    dcc.Graph(
        id='downtime_breakdown',
        figure=downtime_fig_pie
    ),

])

@app.callback(
    Output(component_id='output_downtime_graph', component_property='figure'),
    Output(component_id='data_table', component_property='data'),
    Output(component_id='downtime_breakdown', component_property='figure'),
    Output(component_id='downtime_table', component_property='data'),
    Input(component_id='data_date', component_property='value'),
    Input(component_id='data_line', component_property='value'),
    Input(component_id='data_workcell', component_property='value')
)
def update_output_graph(data_date, data_line, data_workcell):
    print(data_date, data_line, data_workcell)

    # Update Hourly output bar chart
    # output_fig = px.bar(output_df[data_line][data_workcell].loc[data_date], y="HourlyOutput", text='HourlyOutput')
    
    # Update output data table
    output_data_table_df = output_df[data_line][data_workcell].loc[data_date].copy()
    output_data_table_df.reset_index(inplace=True)
    output_data_table_df['NGRate'] = output_data_table_df['NGRate'].apply(make_float)
    output_data_table_df['Yield'] = output_data_table_df['Yield'].apply(make_float)
    output_data_table_df['YieldWithoutSample'] = output_data_table_df['YieldWithoutSample'].apply(make_float)
    output_data_table_df = output_data_table_df.rename(columns = {'index':'new column name'})

    # Upddate pie chart
    default_downtime_breakdown_df = downtime_date_dict[data_line][data_date]['downtime_breakdown'][f'wc{data_workcell + 1}']
    default_breakdown_pie_df = pd.DataFrame(default_downtime_breakdown_df)
    default_breakdown_pie_df[f'wc{data_workcell + 1}'] = pd.to_timedelta(default_breakdown_pie_df[f'wc{data_workcell + 1}'])
    default_breakdown_pie_df["total_seconds"] = np.round(default_breakdown_pie_df[f'wc{data_workcell + 1}'].dt.total_seconds(), 0)
    downtime_fig_pie = px.pie(default_breakdown_pie_df, values='total_seconds', names=default_breakdown_pie_df.index)

    # Update downtime breakdown table
    downtime_data_table_df = default_breakdown_pie_df.copy()
    downtime_data_table_df = default_breakdown_pie_df.rename({f'wc{data_workcell + 1}': 'total_time'}, axis=1)
    downtime_data_table_df['total_time'] = downtime_data_table_df['total_time'].astype(str)
    downtime_data_table_df.reset_index(inplace=True)
    downtime_data_table_df = downtime_data_table_df.rename(columns = {'index':'new column name'})

    # Update Hourly downtime line chart
    default_hourly_downtime_df = downtime_date_dict[data_line][data_date]["hourly_downtime"][downtime_date_dict[data_line][data_date]["hourly_downtime"]['WORKCELL'] == (data_workcell + 1)]
    # downtime_fig = px.line(default_hourly_downtime_df, x=default_hourly_downtime_df.index, y='Total_minutes')

    # Update Hourly output downtime figure
    mul_fig = make_subplots(specs=[[{"secondary_y": True}]])
    # Add traces
    mul_fig.add_trace(
        go.Bar(x=output_df[data_line][data_workcell].loc[data_date].index, y=output_df[data_line][data_workcell].loc[data_date]["HourlyOutput"], name="Hourly output", text=output_df[data_line][data_workcell].loc[data_date]["HourlyOutput"]),
        secondary_y=False,
    )

    mul_fig.add_trace(
        go.Scatter(x=default_hourly_downtime_df.index, y=default_hourly_downtime_df['Total_minutes'], name="Downtime in minutes"),
        secondary_y=True,
    )

    # Add mul_figure title
    mul_fig.update_layout(
        title_text="Hourly output and downtime in minutes"
    )

    # Set x-axis title
    mul_fig.update_xaxes(title_text="Createtime")

    # Set y-axes titles
    mul_fig.update_yaxes(title_text="<b>Output</b>", secondary_y=False)
    mul_fig.update_yaxes(title_text="<b>Downtime</b> in minutes", secondary_y=True)


    return mul_fig, output_data_table_df.to_dict('records'), downtime_fig_pie, downtime_data_table_df.to_dict('records')

if __name__ == '__main__':
    # app.run_server(debug=True)
    app.run_server(host='0.0.0.0', debug=True, port='80')

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import os
import re
from glob import glob

import dash
import pandas as pd
import plotly.express as px
from dash import dash_table, dcc, html
from dash.dependencies import Input, Output

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

df_arr = {}
for x in output_files_name:
    arr = []
    for y in range(10):
        arr.append(pd.read_excel(x, sheet_name=y, parse_dates=["Createtime"], index_col="Createtime"))
    line_name = re.search('L.{1}', x).group(0)
    df_arr[line_name] = arr

date_arr = list(set([x.date() for x in df_arr[output_lines_name[0]][0].index]))
date_arr.sort()
date_str_arr = [d.strftime("%m/%d/%Y")  for d in date_arr]

fig = px.bar(df_arr[output_lines_name[0]][0].loc[date_str_arr[0]], y="HourlyOutput", text='HourlyOutput')

# fig.update_layout(
#     plot_bgcolor=colors['background'],
#     paper_bgcolor=colors['background'],
#     font_color=colors['text']
# )

df_test = df_arr[output_lines_name[0]][0].loc[date_str_arr[0]].copy()
df_test.reset_index(inplace=True)
df_test = df_test.rename(columns = {'index':'new column name'})

app.layout = html.Div(children=[
    html.H1(
        children='POD Hourly Output',
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

    dcc.Graph(
        id='hourly_output',
        figure=fig
    ),

    html.H2(
        children='Table Details',
        style={
        'textAlign': 'center',
        'color': colors['text']
    }),

    dash_table.DataTable(
        id='data_table',
        columns=[{"name": i, "id": i} for i in df_test.columns],
        data=df_test.to_dict('records'),
    )

])

@app.callback(
    Output(component_id='hourly_output', component_property='figure'),
    Output(component_id='data_table', component_property='data'),
    Input(component_id='data_date', component_property='value'),
    Input(component_id='data_line', component_property='value'),
    Input(component_id='data_workcell', component_property='value')
)
def update_graph(data_date, data_line, data_workcell):
    print(data_date, data_line, data_workcell)
    fig = px.bar(df_arr[data_line][data_workcell].loc[data_date], y="HourlyOutput", text='HourlyOutput')
    df_test = df_arr[data_line][data_workcell].loc[data_date].copy()
    df_test.reset_index(inplace=True)
    df_test = df_test.rename(columns = {'index':'new column name'})

    return fig, df_test.to_dict('records')

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True)

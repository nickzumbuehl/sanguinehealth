import pandas as pd
import plotly.express as px  # (version 4.7.0 or higher)
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, dash_table  # pip install dash (version 2.0.0 or higher)
import os
import numpy as np
import dash_bootstrap_components as dbc


app = Dash(__name__, external_stylesheets=[dbc.themes.LUX, dbc.icons.FONT_AWESOME, dbc.icons.BOOTSTRAP])
server = app.server

url_list = [
    "https://drive.google.com/file/d/17XeEf6NqDPRmoZG7DUA_A5SStmQEx5PD/view?usp=sharing",
    "https://drive.google.com/file/d/1JHkTW9uUDV8rB08Pf003KOLfyQPis8nN/view?usp=sharing"
]
url_list = ["burn_out_test.csv", "burn_out_train.csv"]

url_list = [
    "https://raw.githubusercontent.com/nickzumbuehl/sanguinehealth/master/burn_out_train.csv",
    "https://raw.githubusercontent.com/nickzumbuehl/sanguinehealth/master/burn_out_test.csv"
]

df_bo = pd.DataFrame()
for url in url_list:
    # path = 'https://drive.google.com/uc?export=download&id=' + url.split('/')[-2]
    #path = os.path.join(path_base, url)

    df_bo = pd.concat([df_bo, pd.read_csv(url)])

# DATA ENHANCEMENT => Adding team to Employee
df_t = df_bo.reset_index().rename(columns={"index": "identifier"})
df_t = df_t.assign(emp_tmp="E")
df_t = df_t.assign(emp_code=lambda x: x.emp_tmp + x.identifier.astype(str)).drop(columns=["identifier", "emp_tmp"])

team_size = 20

df_t = df_t.assign(
    team_ind=lambda x: (pd.Series(list(range(int(df_t.shape[0]/team_size))) * team_size)).astype(str),
    team_tmp="T"
)
df_t = df_t.assign(team=lambda x: x.team_tmp + x.team_ind).drop(columns=["team_ind", "team_tmp"])

df_t = df_t.dropna()

df_t = df_t.rename(columns={"Mental Fatigue Score": "mental_fatigue_score"})

labels = ["<2", "2-4", "4-6", "6-8", ">8"]
df_t = df_t.assign(
    mfs_bucket=lambda x: pd.qcut(x.mental_fatigue_score,q=[0, .2, .4, .6, .8, 1],labels=labels,),
    helper_ones = 1
)

# APP LAYOUT
sidebar = html.Div(
    className="sidebar",
    children=[
        html.I(className="fa-regular fa-face-swear"),
        html.I(className="bi bi-info-circle-fill me-2"),
        html.H4("Mental Health Monitor"),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink("Executive Summary", href="/", active="exact"),
                dbc.NavLink("Team & Employee View", href="/page-1", active="exact"),
                dbc.NavLink("Causes", href="/page-2", active="exact"),
            ],
            vertical=True,
            pills=True,
        ),
    ],
)

content = html.Div(
    className="content",
    id="page-content",
)

app.layout = html.Div(
    children=[dcc.Location(id="url"), sidebar, content]
)


# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Dash Components
@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname == "/":
        return display_exec_summary()
    elif pathname == "/page-1":
        return display_team_employee_view()
    elif pathname == "/page-2":
        return html.P("Oh cool, this is page 2!")


@app.callback(
    Output(component_id="team_plt", component_property="figure"),
    [Input(component_id="slct_team", component_property="value")]
)
def team_plot(slct_team):

    if not type(slct_team) == list:
        slct_team = [slct_team]

    df_d = df_t[lambda x: x.team.isin(slct_team)]

    fig = px.bar(
        df_d.sort_values(by="mental_fatigue_score", ascending=True),
        x="mental_fatigue_score",
        y="emp_code",
        color="team",  # Designation
        orientation='h',
        title="MFS of Team Members",
        color_discrete_sequence=px.colors.qualitative.Set3
    )

    return fig


@app.callback(
    Output(component_id="corr_tenure_mfs", component_property="figure"),
    [Input(component_id="slct_team", component_property="value")]
)
def plt_corr_tenure_mfs(slct_team):

    if not type(slct_team) == list:
        slct_team = [slct_team]

    df_d = df_t[lambda x: x.team.isin(slct_team)]

    fig = px.scatter(
        df_d, x="Designation", y="mental_fatigue_score",
        color="Resource Allocation",
        title="Correlation of Level of Seniority & MSF",
        color_discrete_sequence=px.colors.qualitative.Set3
    )

    return fig


# ----------- helper functions
def display_exec_summary():
    return (
        [
            dbc.Row(
                className="",
                children=[
                    dbc.Col(className="container-item", children=display_average_stress_level(), xl=5),
                    dbc.Col(className="container-item", children=[dcc.Graph(figure=display_exec_graph())], xl=6)
                ]
            ),
            dbc.Row(
                className="",
                children=[
                    dbc.Col(className="container-item", children=[dcc.Graph(figure=display_team_graph())], xl=5),
                    dbc.Col(className="container-item", children=[dcc.Graph(figure=display_pie_chart_mfs())], xl=6)
                ]
            ),
        ]
    )


def display_team_employee_view():
    return (
        [
            dbc.Row(
                children=[
                    dbc.Col(
                        className="container-item",
                        children=[
                            html.P("Select teams to be analyzed"),
                            dcc.Dropdown(
                                className="padding",
                                id="slct_team",
                                options=[{"label": i, "value": i} for i in set(df_t.team)],
                                multi=True,
                                value="T0",
                                style={'width': "100%"}),
                        ]
                    ,md=5),
                    dbc.Col(className="container-item", children=[dcc.Graph(id='team_plt', figure={})], md=6)
                ]
            ),
            dbc.Row(
                children=[
                    dbc.Col(className="container-item", children=[dcc.Graph(figure=display_team_graph())], md=5),
                    dbc.Col(className="container-item", children=[dcc.Graph(id='corr_tenure_mfs', figure={})], md=6)
                ]
            ),
        ]
    )


def display_average_stress_level():

    columns_selected = ["emp_code", "team", "Designation", "Resource Allocation", "Burn Rate"]

    df_d = df_t[lambda x: x["Burn Rate"] != 1].sort_values(by=["Burn Rate"], ascending=False).head(15)

    # mean_stress = np.round(df_t.mental_fatigue_score.astype(float).mean(), 2)
    #
    # return (
    #     html.Div(
    #         className="boxtext",
    #         children=[
    #             html.P(f"Average Mental Fatigue Score (MFS) of your Employees is {mean_stress}"),
    #         ])
    # )

    return (
        dbc.Row(children=[html.P("Employees most likely to burn")]),
        dbc.Row(dash_table.DataTable(df_d.to_dict('records'), [{"name": i, "id": i} for i in columns_selected]))
    )


def display_team_graph():
    df_d = df_t.groupby(by=["team"]).agg(
        {"mental_fatigue_score": 'mean'}).reset_index().head(20)

    fig = px.bar(
        df_d.sort_values(by="mental_fatigue_score", ascending=True),
        x="mental_fatigue_score",
        y="team",
        orientation='h',
        title="MFS of most stressed teams",
        color_discrete_sequence=px.colors.qualitative.Set3
    )

    return fig


def display_exec_graph():

    fig = px.histogram(
        df_t[lambda x: x.mental_fatigue_score != 100.0],
        x="mental_fatigue_score",
        color="Gender",
        title="Distribution of MFS",
        color_discrete_sequence=px.colors.qualitative.Set3
    )

    return fig


def display_pie_chart_mfs():

    fig = px.pie(
        df_t,
        values='helper_ones',
        names='mfs_bucket',
        color_discrete_sequence=px.colors.qualitative.Set3,
        title='MFS by Groups')

    return fig


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=False, port=7777)

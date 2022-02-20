import pandas as pd
import plotly.express as px  # (version 4.7.0 or higher)
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output  # pip install dash (version 2.0.0 or higher)
import os
import numpy as np
import dash_bootstrap_components as dbc


app = Dash(__name__, external_stylesheets=[dbc.themes.LUX])

path_base = "/Users/zumbuehlnick/Documents/DashAppTutorial"
file_name = "IHME-GBD_2019_DATA-1c06533e-1.csv"
file_name_mental_inst = "mental_institutions.csv"


url_list = [
    "https://drive.google.com/file/d/17XeEf6NqDPRmoZG7DUA_A5SStmQEx5PD/view?usp=sharing",
    "https://drive.google.com/file/d/1JHkTW9uUDV8rB08Pf003KOLfyQPis8nN/view?usp=sharing"
]
url_list = ["burn_out_test.csv", "burn_out_train.csv"]

df_bo = pd.DataFrame()
for url in url_list:
    # path = 'https://drive.google.com/uc?export=download&id=' + url.split('/')[-2]
    path = os.path.join(path_base, url)
    df_bo = pd.concat([df_bo, pd.read_csv(path)])

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

df_mi = pd.read_csv(os.path.join(path_base, file_name_mental_inst))
df_mi = df_mi.rename(columns={
    "Mental hospitals (per 100 000 population)":  "nr_hostpitals_per_100K",
    "Country": "country"
})

df_mh = pd.read_csv(os.path.join(path_base, file_name))
df_mh = df_mh[lambda x: (x.measure_id == 6) & (x.metric_id == 2)]

# ------------------------------------------------------------------------------
# # App layout
# app.layout = html.Div(
#     className="borderdev",
#     children=[
#         html.H1("Dashboard Template: Mental Health & Anxiety", className="padding"),
#         dbc.Row(
#             className="padding border",
#             children=[
#                 dbc.Col([
#                     dcc.Dropdown(
#                         className="padding",
#                         id="slct_cause",
#                         options=[{"label": i, "value": i} for i in set(df_mh.cause_name)],
#                         multi=False,
#                         value="Mental disorders",
#                         style={'width': "100%"}
#                     ),
#                     dcc.Dropdown(
#                         className="padding",
#                         id="slct_country",
#                         options=[{"label": i, "value": i} for i in set(df_mh.location_name)],
#                         multi=True,
#                         value="Global",
#                         style={'width': "100%"}
#                     ),
#                 ]),
#                 dbc.Col(
#                     children=[dcc.Graph(id='my_bee_map', figure={})],
#                 ),
#             ]
#         ),
#         dbc.Row(
#             className="padding border",
#             children=[
#                 dbc.Col([
#                     dcc.Dropdown(
#                         className="padding",
#                         id="slct_bar_country",
#                         options=[{"label": i, "value": i} for i in set(df_mi.country)],
#                         multi=True,
#                         value=list(set(df_mi.country)),  # ["Australia", "Switzerland", "China", "Japan"],
#                         style={'width': "100%"})]
#                 ),
#                 dbc.Col(
#                     children=[dcc.Graph(id='bar_plot', figure={})],
#                 )
#             ]
#         )
#     ]
# )

sidebar = html.Div(
    className="sidebar",
    children=[
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
    Output(component_id='my_bee_map', component_property='figure'),
    [Input(component_id='slct_cause', component_property='value'),
     Input(component_id='slct_country', component_property='value')]
)
def update_graph(option_slctd, slct_country):

    if not type(slct_country) == list:
        slct_country = [slct_country]

    df = df_mh.copy()

    df = df[lambda x: (x.cause_name == option_slctd) & (x.location_name.isin(slct_country))].sort_values(
        by=["location_name", "year"], ascending=True)

    fig = px.line(df, x='year', y="val", color="location_name")

    return fig


@app.callback(
    Output(component_id="bar_plot", component_property="figure"),
    [Input(component_id="slct_bar_country", component_property="value")],
)
def update_bar_chart(slct_bar_country):

    if not type(slct_bar_country) == list:
        slct_bar_country = [slct_bar_country]

    df = df_mi[lambda x: x.country.isin(slct_bar_country)].sort_values(by="nr_hostpitals_per_100K", ascending=False)

    bar_fig = px.bar(df, x='country', y='nr_hostpitals_per_100K')

    return bar_fig


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


# ----------- helper functions
def display_exec_summary():
    return (
        [
            dbc.Row(
                className="",
                children=[
                    dbc.Col(className="container-item center_sub_div", children=display_average_stress_level(), md=5),
                    dbc.Col(className="container-item", children=[dcc.Graph(figure=display_exec_graph())], md=6)
                ]
            ),
            dbc.Row(
                className="",
                children=[
                    dbc.Col(className="container-item", children=[dcc.Graph(figure=display_team_graph())], md=5),
                    dbc.Col(className="container-item", children=[dcc.Graph(figure=display_executive_distribution())], md=6)
                ]
            ),
        ]
    )


def display_team_employee_view():
    """
    select X number of teams | or select
    :return:
    """
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
                    dbc.Col(className="container-item", children=[dcc.Graph(figure=display_executive_distribution())], md=6)
                ]
            ),
        ]
    )


def display_average_stress_level():

    mean_stress = np.round(df_t.mental_fatigue_score.astype(float).mean(), 2)

    return (
        html.Div(
            className="boxtext",
            children=[
                html.P(f"Average Mental Fatigue Score (MFS) of your Employees is {mean_stress}"),
            ])
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


def display_executive_distribution():

    df_d = df_t[lambda x: x.Designation >= 4]

    fig = px.histogram(
        df_d,
        x="mental_fatigue_score",
        color="Gender",
        title="Distribution of MFS for Mid & Top Management",
        color_discrete_sequence=px.colors.qualitative.Set3
    )

    return fig


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True, port=7777)

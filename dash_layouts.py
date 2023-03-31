from dash import html, dcc
import dash_bootstrap_components as dbc
import dash_tabulator
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from datetime import datetime
import utilities
from app_init import app
import pandas as pd
import yaml


# Dash layouts
# ----------------------------------------------------------------------------
def map_segment(
    places: pd.DataFrame,
    local : bool
) -> html:

    highest_altitude = places['altitude'].max()
    highest_altitude -= highest_altitude % -1000
    altitude_steps = list(set(list(range(0, highest_altitude, 1000)) + [highest_altitude]))
    altitude_steps.sort()

    layout = html.Div([

        dmc.Group([
            dmc.Button(
                id       = 'add_new_place',
                disabled = not(local),
                leftIcon = DashIconify(icon="material-symbols:add-location-alt-outline", width=20)
            ),        
            dmc.Button(
                id       = "filter_map",
                leftIcon = DashIconify(icon="material-symbols:filter-list", width=20)),
        ], spacing='xs'),
        html.Br(),

        dbc.Collapse([

            dbc.Card([
                dbc.CardBody([
        
                    dbc.Row([
                        dbc.Col([ 
                            dmc.Select(
                                id          = "search_place", 
                                icon        = DashIconify(icon="ic:outline-search", width=20),
                                placeholder = "Selectionne un lieu...",
                                searchable  = True, 
                                clearable   = True),
                        ], width= 2),

                        dbc.Col([ 
                            dmc.MultiSelect(
                                id          = "category_selection", 
                                placeholder = "Selectionn un type de lieux...",
                                searchable  = True, 
                                clearable   = True,
                                value       = [ cat for cat in places['category'].unique()],
                                data        = [ cat for cat in places['category'].unique()]),
                        ], width = 4),

                        dbc.Col([     
                            dmc.RangeSlider(
                            id        = 'altitude_slider',
                            min       = 0,
                            max       = 5000,
                            value     = [0, 5000],
                            marks     = [{"value": step, "label":f"{step} m"} for step in altitude_steps]
                            ),

                        ], width = 6),
                    ]),
                ]),
            ]),

        ], id ='collapse_map_filter'),

        html.Br(), 
        dcc.Graph(id='place_map'), 

        dbc.Modal(
            [
                dbc.ModalHeader(
                    dbc.ModalTitle("Add a new place"),
                    close_button=True
                ),
                dbc.ModalBody([
                
                    dmc.TextInput(
                        label    = 'Waypoint',
                        id       = 'new_place_name',
                        placeholder='Type a name...',
                        required = True, 
                        icon     = DashIconify(icon="grommet-icons:waypoint")
                    ),
                    html.Br(),
                    
                    dmc.NumberInput(
                        label     = 'Latitude (WGS 84)',
                        id        = 'new_place_latitude',
                        placeholder='Type a latitude, e.g. 45,97640',
                        step      = 0.00001,
                        precision = 5,
                        required  = True, 
                        icon      = DashIconify(icon="mdi:latitude")
                        ),
                    html.Br(),

                    dmc.NumberInput(
                        label     = 'Longitude (WGS 84)',
                        id        = 'new_place_longitude',
                        placeholder='Type a longitude, e.g. 7,65861',
                        step      = 0.00001,
                        precision = 5,
                        required  = True, 
                        icon      = DashIconify(icon="mdi:longitude"),
                    ),
                    html.Br(), 

                    dmc.NumberInput(
                        label = 'Altitude',
                        id    = 'new_place_altitude',
                        placeholder ='Type an altitude in meter, e.g. 4478',
                        step  = 1,
                        required = True, 
                        icon  = DashIconify(icon="material-symbols:altitude-outline"),
                    ),
                    html.Br(),                                        

                    dmc.Select(
                        id    = 'new_place_category',
                        label = "Category",
                        data  = [{"value": item.lower(), "label": item} for item in ['Summit', 'Pass', 'Hut', 'POI', 'Cliff'] ],
                        icon  = DashIconify(icon="material-symbols:category"),
                        required = True, 
                    ),

                ]),
                dbc.ModalFooter(
                    dmc.Group([
        
                        dmc.Alert(
                            title           = "Well done!",
                            id              = "alert_new_place_saved",
                            color           = "green",
                            hide            = True,
                            withCloseButton = True,
                        ),

                        dmc.Button("Save",
                        id       = "save_new_place",
                        leftIcon = DashIconify(icon="ri:save-3-fill", width=20),
                        disabled = True),
                    ])
                ),
            ],
            id      = "modal_new_place",
            is_open = False,
        )

    ])

    return layout


# ----------------------------------------------------------------------------
def activities_segment(
    places    : pd.DataFrame,
    metadata  : dict,
    local     : bool,
    language  : str
) -> html:

    waypoints = places['waypoint'].unique()
    waypoints.sort()

    activity_categories = list(metadata['activity'].keys())
    activity_categories.sort()

    roles = list(metadata['role'])
    roles.sort()

    contexts = list(metadata['context'])
    contexts.sort()  

    translation = utilities.translation

    layout = html.Div([

        dmc.Group([
            dmc.Button(
                id       = 'new_activity',
                disabled = not(local),
                leftIcon = DashIconify(icon="ic:baseline-new-label", width=20)
            ),
            dmc.Button(
                id       = 'filter_activities',
                leftIcon = DashIconify(icon="material-symbols:filter-list", width=20)
            ),            
        ]),

        dbc.Collapse([
            html.Br(),
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dmc.Select(
                                id         = 'filter_activity_waypoints',
                                placeholder= 'Selectionne un lieu...',
                                data       = waypoints,
                                searchable = True, 
                                clearable  = True
                            )
                        ], width = 3)
                    ])
                ])
            ]),
        ], id ='collapse_activities_filter'),

        html.Br(),
        dbc.Row([
            
            dbc.Col([
                dash_tabulator.DashTabulator(
                    id      = 'activities_tabulator',
                    theme   = 'tabulator_simple',
                    options = {'pagination': 'local', 'paginationSize': 200, 'height': 630, 'selectable': 1},
                ),
            ], id='activity_table', width = 12),
            
            dbc.Col([     
                html.Div([
                    dmc.Grid(
                        children=[
                            dmc.Col(
                                dmc.ThemeIcon(
                                    size     = "xl",
                                    color    = "indigo",
                                    variant  = "filled",
                                    children = DashIconify(id='selected_activity_icon', icon= "mdi:ski", width=25), # it needs a default value...
                             ), span=1),
                            dmc.Col([
                                dmc.Badge(id='details_days'),
                                dmc.Badge(id='details_grade')]
                            , span=3),

                            dmc.Col(
                                dmc.ActionIcon(
                                    DashIconify(icon="material-symbols:edit-document-outline", width=30),
                                    disabled = not(local),
                                    size     = "xl",
                                    variant  = "outline",
                                    id       = "edit_activity",)
                            , span=1, offset=7),
                        ],
                        gutter="xl",
                    ),                         

                    html.Hr(),
                    dmc.Group([
                        dmc.List(
                            id      = 'selected_activity_waypoints',
                            size    = 'sm',
                            spacing = 'sm',
                        ),
                        dmc.Divider(orientation="vertical", style={"height": 100}),
                        dmc.Text(id='details_comments', color='gray')
                    ]),

                    html.Hr(),
                    html.A(id='details_topo'),     
                        
                ], id='div_activity_details', style={'display': 'none'})

            ], id='activity_details', width = 0),
        ]),

        dbc.Modal(
            [
                dbc.ModalHeader(
                    dbc.ModalTitle(id='activity_modal_title'),
                    close_button=True
                ),
                dbc.ModalBody([
                
                    dmc.TextInput(
                        label = 'Label',
                        id    = 'new_activity_label',
                        placeholder='Type a name',
                        icon   = DashIconify(icon="grommet-icons:waypoint"),
                        required = True, 
                    ),
                    html.Br(), 

                    dmc.MultiSelect(
                        id         = 'new_activity_waypoints',
                        label      = "Waypoints",
                        data       = [waypoint for waypoint in waypoints],
                        icon       = DashIconify(icon="ic:outline-place"),
                        searchable = True, 
                        clearable  = True,
                        required   = True, 
                    ),
                    html.Br(),                    

                    dbc.Row([
                        dbc.Col([
                            dmc.Select(
                                id    = 'new_activity_category',
                                label = "Category",
                                data  = [{"value": item, "label": translation['activities'][item][language]} for item in activity_categories ],
                                icon  = DashIconify(icon="material-symbols:category"),
                                required = True, 
                            ),
                        ], width=6),

                        dbc.Col([
                            dmc.Select(
                                id    = 'new_activity_grade',
                                label = "Grade",
                                icon  = DashIconify(icon="game-icons:armor-upgrade"),
                                required = True, 
                            ),
                        ], width=6),                            
                    ]),
                    html.Br(),

                    dbc.Row([
                        dbc.Col([
                            dmc.DatePicker(
                                id          = "new_activity_date",
                                label       = "Start Date",
                                style       = {"width": 200},
                                required = True, 
                            ),
                        ], width = 6),
                        dbc.Col([                        
                            dmc.NumberInput(
                                label       = 'Days',
                                id          = 'new_activity_days',
                                placeholder = 'Type a number of days',
                                precision   = 1,
                                step        = 0.5,
                                value       = 1,
                                icon        = DashIconify(icon="game-icons:duration"),
                                required    = True, 
                            ),                            
                        ], width = 6),
                    ]),
                    html.Br(), 
                    
                    dbc.Row([

                        dbc.Col([
                            dmc.NumberInput(
                                label     = 'Participants',
                                id        = 'new_activity_participants',
                                placeholder='Type a number of participants',
                                value     = 1,
                                step      = 1,
                                icon      = DashIconify(icon="mdi:people-group"),
                            ),
                        ], width=4),
                        dbc.Col([
                            dmc.Select(
                                id       = 'new_activity_context',
                                label    = "Context",
                                data     = [{"value": item, "label": translation['contexts'][item][language]} for item in contexts ],
                                icon     = DashIconify(icon="material-symbols:category"),
                                required = True, 
                            ),
                        ], width=4),                            
                        
                        dbc.Col([
                            dmc.Select(
                                id       = 'new_activity_role',
                                label    = "Role",
                                data     = [{"value": item, "label": translation['roles'][item][language]} for item in roles ],
                                icon     = DashIconify(icon="material-symbols:category"),
                                required = True, 
                            ),
                        ], width=4),                          
                    ]),
                    html.Br(),
                
                    dbc.Row([
                        dbc.Col([
                            dmc.TextInput(
                                label       = 'Topo',
                                id          = 'new_activity_topo',
                                placeholder = 'Type a URL...',
                                icon        = DashIconify(icon="grommet-icons:waypoint")
                            ),
                        ], width= 6),
                        dbc.Col([
                            dmc.TextInput(
                                label       = 'Blog/Youtube',
                                id          = 'new_activity_blog',
                                placeholder = 'Type a URL...',
                                icon        = DashIconify(icon="grommet-icons:waypoint")
                            ),
                        ], width= 6),                        
                    ]),
                    html.Br(), 

                    dmc.TextInput(
                        label       = 'Comment',
                        id          = 'new_activity_comment',
                        placeholder = 'Type a comment, if any',
                        icon        = DashIconify(icon="material-symbols:add-comment-outline")
                    ),
                    html.Br(), 

                ]),
                dbc.ModalFooter(
                    dmc.Group([
        
                        dmc.Alert(
                            title           = "Well done!",
                            id              = "alert_new_activity_saved",
                            color           = "green",
                            hide            = True,
                            withCloseButton = True,
                        ),

                        dmc.Button("Save",
                        id       = "save_new_activity",
                        leftIcon = DashIconify(icon="ri:save-3-fill", width=20),
                        disabled = True),
                    ])
                ),
            ],
            id      = "modal_new_activity",
            is_open = False,
            size    = 'lg'
        )
    ])

    return layout


# ------------------------------------------------------------------------------------------------
# STATS
# ------------------------------------------------------------------------------------------------
def stats_segment(
    language
) -> html:
    
    layout = html.Div([
                
        dmc.SegmentedControl(
            id    = "stats_segments",
            data  = [],
            value = 'stats_places',
            color = "orange",
        ),

        html.Div([     
            dmc.Center(     
                dmc.RadioGroup(
                    id    = "places_plot_switch",
                    value = "exploded_view",
                    orientation = "horizontal",
                ),
            ),
            html.Div([
                dcc.Graph(id='places_plot'),
            ], id='places_plot_div', style={'display':'none'}),
            html.Div([
                html.Br(),
                dash_tabulator.DashTabulator(
                    id      = 'places_trivia_tabulator',
                    theme   = 'tabulator_simple',
                    columns = [
                        {'title': '' , 'field': 'category_translated'},
                        {'title': 'Plus basse altitude', 'field': 'lowest'},
                        {'title': 'Plus haute altitude', 'field': 'highest'},
                        {'title': 'Plus visité'        , 'field': 'most_visited'}
                    ]
                ),
            ], id='places_trivia_div', style={'display': 'none'}),

        ], id='stats_places'),

        # Activities plot
        html.Div([
            html.Br(),
            dmc.Switch(
                id      = 'cumulative_activities',
                size    = "sm",
                radius  = "lg",
                label   = "Cumulatif",
                checked = False
            ),
            html.Div(id='test'),
            dcc.Graph(id='activities_plot'),
        ], id='stats_year', style={'display': 'none'}),

        # Grades plot
        html.Div(id='grades_overtime', style={'display': 'none'}),
        
        # Context plot        
        html.Div([
            dcc.Graph(id='context_overtime'),            
        ], id='stats_context', style={'display': 'none'}),      

    ])
    
    return layout


# Main layout
# ----------------------------------------------------------------------------
def main_layout(
    local,
    language = 'fr'
) -> html:

    with open('settings/metadata.yaml') as file:
        metadata = yaml.load(file, Loader=yaml.FullLoader)

    # Load visited places and activities
    places, activities = utilities.load_data(metadata)

    places_df = utilities.places_dict_to_df(places)

    activities_df = utilities.places_dict_to_df(activities)
    activities_no_waypoints = activities_df[activities_df['waypoints'].isnull()]
    #print(activities_no_waypoints[['label', 'date']].to_string())

    layout = html.Div([
        
        dcc.Store(
            id   = 'places_store',
            data = places
        ),

        dcc.Store(
            id   = 'activities_store',
            data = activities
        ),

        dcc.Store(
            id   = 'metadata_store',
            data = metadata
        ),

        html.Div(
            language,
            id    = 'language',
            style = {'display': 'none'}
        ),

        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                            
                        dmc.Center(html.Img(src=app.get_asset_url('logo.png'), height='110px')),
                        dmc.Center(dmc.Text("- because it's there -", color='lightblue', size='xs')),

                        html.Hr(),
                        dmc.SegmentedControl(
                            id          = "navigation_segments",
                            data        = [],
                            value       = 'map',
                            color       = "orange",
                            orientation = 'vertical',
                            fullWidth   = True
                        ),

                        # Totals
                        html.Br(),
                        dmc.SimpleGrid(
                            cols=2,
                            children=[
                                dmc.Text(id='days_total_text', size='xs', color='gray'),
                                dmc.Badge(id='days_total', color="blue")
                            ]
                        ),

                        dmc.SimpleGrid(
                            cols=2,
                            children=[
                                dmc.Text(id='activities_total_text', size='xs', color='gray'),
                                dmc.Badge(id='activities_total', color="blue")
                            ]
                        ),

                        dmc.SimpleGrid(
                            cols=2,
                            children=[
                                dmc.Text(id='summits_total_text', size='xs', color='gray'),
                                dmc.Badge(id='summits_total', color="blue")
                            ]
                        ),

                        dmc.SimpleGrid(
                            cols=2,
                            children=[
                                dmc.Text(id='passes_total_text', size='xs', color='gray'),
                                dmc.Badge(id='passes_total', color="blue")
                            ]
                        ),


                        dmc.SimpleGrid(
                            cols=2,
                            children=[
                                dmc.Text(id='huts_total_text', size='xs', color='gray'),
                                dmc.Badge(id='huts_total', color="blue")
                            ]
                        ),                   

                        html.Hr(),
                        dmc.Group([
                                dmc.ActionIcon(
                                    DashIconify(icon="material-symbols:language-french-rounded", width=20),
                                    size="lg",
                                    id="language_fr",
                                    variant='outline',
                                ),  html.Br(),
                                dmc.ActionIcon(
                                    DashIconify(icon="ri:english-input", width=20),
                                    size="lg",
                                    id="language_en",
                                ), 
                        ], align='center', grow=True, position='center'),

                    ], width=1),

                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div(
                                    id       = 'map_content',
                                    children = map_segment(places_df, local)),
                                html.Div(
                                    id       = 'activities_content', 
                                    children = activities_segment(places_df, metadata, local, language),
                                    style    = {'display':'none'}),
                                html.Div(
                                    id       = 'stats_content',
                                    children = stats_segment(language),
                                    style    = {'display':'none'})
                            ])
                        ])
                    ], width=11),
                ]),
                html.Br(),
                dmc.Footer(
                    height=25,
                    fixed=True,
                    children=[dmc.Text("Nicolas Dupuis, 2023. Powered by Dash-Plotly & Python.", color='white', size='sm')],
                    style={"backgroundColor": "#4169e1"},
                )
            ])
        ])
    ])

    return layout
from dash import Input, Output, State, ctx, dcc
from dash import html
from app_init import app
import utilities
import pandas as pd
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import dash_bootstrap_components as dbc
import math
from functools import reduce


# Switch tab
#----------------------------------------------------------------------------
@app.callback(
    [Output('map_content',        'style'),
     Output('activities_content', 'style'),
     Output('stats_content',      'style')],
     Input('navigation_segments', 'value')
    )
def switch_layout(layout):

    layout_map        = {'display': 'none'}
    layout_activities = {'display': 'none'}
    layout_stats      = {'display': 'none'}

    if layout=='map' or layout==None:
        layout_map={}
    
    elif layout=='activities':
        layout_activities = {}
    
    elif layout=='stats':
        layout_stats = {}

    return (
        layout_map,
        layout_activities,
        layout_stats
    )

# Switch stats
#----------------------------------------------------------------------------
@app.callback(
    [Output('stats_places',   'style'),
     Output('stats_year',     'style'),
     Output('grades_overtime','style'),
     Output('stats_context',  'style')],
     Input ('stats_segments', 'value')
)
def switch_stats(stat):

    layout_places  = {'display': 'none'}
    layout_year    = {'display': 'none'}
    layout_grade   = {'display': 'none'}
    layout_context = {'display': 'none'}

    if stat in ('stats_places', None):
        layout_places={}
   
    elif stat=='stats_year':
        layout_year = {}
    
    elif stat=='stats_grade':
        layout_grade = {}
   
    elif stat=='stats_context':
        layout_context = {}

    return (
        layout_places,
        layout_year,
        layout_grade,
        layout_context,
    )


# Activity selected in tabulator, display details
#----------------------------------------------------------------------------
@app.callback(
    [Output('activity_table',              'width'           ),
     Output('activity_details',            'width'           ),
     Output('div_activity_details',        'style'           ),
     Output('details_days',                'children'        ),
     Output('details_topo',                'href'            ),
     Output('details_topo',                'children'        ),
     Output('details_comments',            'children'        ),
     Output('details_grade',               'children'        ),
     Output('selected_activity_waypoints', 'children'        ),
     Output('selected_activity_icon',      'icon'            )],
     Input ('activities_tabulator',        'multiRowsClicked'),
    [State ('places_store',                'data'            ),
     State ('metadata_store',              'data'            )],
    prevent_initial_call=True
)
def enable_save_new_place(
    row, 
    places_store, metadata_store
):

    if row == []:
        table_width   = 12
        details_width = 0
        div_style     = {'display': 'none'}
        days          = None
        href          = None
        link_label    = None
        comments      = None
        grade         = None
        waypoints     = None
        activity_icon = "mdi:ski" # it needs a default value...
   
    else: 
        table_width   = 6
        details_width = 6
        div_style     = {}
        
        days = f"{row[0]['days']} day"
        if row[0]['days'] > 1: 
            days += 's'
        
        href = row[0]['topo']
        if href:
            if 'camptocamp' in href: 
                link_label = 'Camptocamp'
            elif 'youtube' in href: 
                link_label = 'Youtube'
            elif 'blogger' in href: 
                link_label = 'Blog'
            else: 
                link_label = 'Link'                                
        else: 
            link_label = ''

        comments = row[0]['comments']
        if not comments: 
            comments='Aucun commentaire'
        
        grade = row[0]['grade']

        activity_icon = metadata_store['icons'][row[0]['category']]

        if row[0]['waypoints']:
            selected_waypoints = row[0]['waypoints'].split(', ')
            places = utilities.places_dict_to_df(places_store)
            places = places[places['waypoint'].isin(selected_waypoints)].sort_values(by='altitude', ascending=False)
            places['icon'] = places['category'].map(metadata_store['icons'])
            places['color'] = places['category'].map(metadata_store['waypoint_color'])

            waypoints = html.Div(
                [
                    dmc.ListItem(
                        f"{row['waypoint']} ({row['altitude']} m)",
                        icon=dmc.ThemeIcon(
                            DashIconify(icon=row['icon']),
                            radius = "xl",
                            color  = row['color'],
                            size   = 30)
                    )
                for _, row in places.iterrows()]
            )
        else: 
            waypoints= html.Div()

    return (
        table_width,
        details_width,
        div_style,
        days,
        href,
        link_label,
        comments, 
        grade, 
        waypoints,
        activity_icon,
    )    


# New place, open modal
#----------------------------------------------------------------------------
@app.callback(
    Output('modal_new_place', 'is_open' ),
    Input ('add_new_place',   'n_clicks'),
    prevent_initial_call=True
)
def modal_new_place(
    clicks
):    
    return True


# New place, enable save if all required fields populated
#----------------------------------------------------------------------------
@app.callback(
    Output('save_new_place',       'disabled'),
    [Input ('new_place_name',      'value'   ),
     Input ('new_place_latitude',  'value'   ),
     Input ('new_place_longitude', 'value'   ),
     Input ('new_place_altitude',  'value'   ),
     Input ('new_place_category',  'value'   )],
    State ('places_store',        'data'     ),
    prevent_initial_call=True
)
def enable_save_new_place(
    name, lat, lon, alt, cat,
    places_store
):

    return (name=='' or name in places_store or lat=='' or lon=='' or alt=='' or cat==None)


# Activity, enable save if all required fields populated
#----------------------------------------------------------------------------
@app.callback(
    [Output('save_new_activity',       'disabled'),
     Output('new_activity_grade',      'data'    )],
    [Input ('new_activity_label',      'value'   ),
     Input ('new_activity_category',   'value'   ),
     Input ('new_activity_date',       'value'   ),
     Input ('new_activity_days',       'value'   ),
     Input ('new_activity_context',    'value'   ),
     Input ('new_activity_role',       'value'   ),
     Input ('new_activity_waypoints',  'value'   )],
     State ('metadata_store',          'data'    ),
    prevent_initial_call=True
)
def enable_save_activity(
    label, category, start_date, days, context, role, waypoints,
    metadata
):

    try: 
        grades = list(metadata['activity'][category]['grades'].keys())
    except:
        grades = ['N/A']

    return (
        (label=='' or category==None or start_date==None or days=='' or context==None or waypoints in [None, []] ),
        grades
    )


# New place, save entry
#----------------------------------------------------------------------------
@app.callback(
    [Output('alert_new_place_saved',   'hide' ),
     Output ('new_place_name',         'value'),
     Output ('new_place_latitude',     'value'),
     Output ('new_place_longitude',    'value'),
     Output ('new_place_altitude',     'value'),
     Output ('new_place_category',     'value'),
     Output ('places_store',           'data' ),
     Output ('new_activity_waypoints', 'data' )],
     Input ('save_new_place',          'n_clicks'),
    [State ('new_place_name',          'value'),
     State ('new_place_latitude',      'value'),
     State ('new_place_longitude',     'value'),
     State ('new_place_altitude',      'value'),
     State ('new_place_category',      'value'),
     State ('places_store',            'data' )],
    prevent_initial_call=True
)
def save_new_place(
    clicks, 
    name, lat, lon, alt, cat, places_store
):

    # Load current data and add new one
    places = pd.concat([
        utilities.places_dict_to_df(places_store)[['waypoint', 'latitude','longitude', 'altitude', 'category']], 
        pd.DataFrame([
            {'waypoint': name, 'latitude': lat, 'longitude': lon, 'altitude': alt, 'category': cat}
        ])
    ]).reset_index()[['waypoint', 'latitude','longitude', 'altitude', 'category']]

    # Save to local file
    places.to_json('data_places.json', orient='table', index=False)

    # Populate dropdown
    places_data = places['waypoint'].unique()
    places_data.sort()

    return (
        False,
        '',
        '',
        '',
        '',
        None,
        places.set_index('waypoint').to_dict('index'),
        places_data
    )


# Activity: add/edit
#----------------------------------------------------------------------------
@app.callback(
    [
     Output ('new_activity_label',       'value'   ),
     Output ('new_activity_category',    'value'   ),
     Output ('new_activity_grade',       'value'   ),
     Output ('new_activity_date',        'value'   ),
     Output ('new_activity_days',        'value'   ),
     Output ('new_activity_context',     'value'   ),
     Output ('new_activity_role',        'value'   ),
     Output ('new_activity_waypoints',   'value'   ),
     Output ('new_activity_participants','value'   ),
     Output ('new_activity_topo',        'value'   ),
     Output ('new_activity_comment',     'value'   ),
     Output ('modal_new_activity',       'is_open' ),
     Output ('activity_modal_title',     'children')],
    [Input  ('new_activity',             'n_clicks'),
     Input  ('edit_activity',            'n_clicks')],
    [State  ('new_activity_label',       'value'   ),
     State  ('new_activity_category',    'value'   ),
     State  ('new_activity_grade',       'value'   ),
     State  ('new_activity_date',        'value'   ),
     State  ('new_activity_days',        'value'   ),
     State  ('new_activity_context',     'value'   ),
     State  ('new_activity_role',        'value'   ),
     State  ('new_activity_waypoints',   'value'   ),
     State  ('new_activity_participants','value'   ),
     State  ('new_activity_topo',        'value'   ),
     State  ('new_activity_comment',     'value'   ), 
     State  ('activities_tabulator',     'multiRowsClicked'),
     State  ('activities_store',         'data'    )],
    prevent_initial_call=True
)
def save_new_place(
    new_clicks, edit_clicks,
    label, cat, grade, start_date, days, context, role, waypoints, participants, topo, comments,
    selected_activity, activities_store
):
    
    open_modal = True

    if ctx.triggered_id == 'new_activity':
        modal_title = 'Enter a new activity'
        label      = ''
        cat        = None
        grade      = None
        start_date = None
        days       = 1
        context    = None
        role       = None
        waypoints  = None
        topo       = None
        comments   = None

    # Edit: load values in the field, using the store
    elif ctx.triggered_id == 'edit_activity':

        id = selected_activity[0]['id']
        raw_activity = activities_store[id]

        modal_title  = 'Edit this activity'
        label        = raw_activity['label']
        cat          = raw_activity['category']
        grade        = raw_activity['grade']
        start_date   = raw_activity['date']
        days         = raw_activity['days']
        context      = raw_activity['context']
        role         = raw_activity['role']
        topo         = raw_activity['topo']
        comments     = raw_activity['comments']
        participants = raw_activity['participants']        
        try: 
            waypoints = raw_activity['waypoints'].split(', ')
        except: # handle my dirty legacy data
            waypoints = []

    return (
        label, cat, grade, start_date, days, context, role, waypoints, participants, topo, comments,
        open_modal,
        modal_title
    )


# Activity: save
#----------------------------------------------------------------------------
@app.callback(
    [Output ('alert_new_activity_saved', 'hide'    ),
     Output ('activities_store',         'data'    )],
     Input  ('save_new_activity',        'n_clicks'),
    [State  ('new_activity_label',       'value'   ),
     State  ('new_activity_category',    'value'   ),
     State  ('new_activity_grade',       'value'   ),
     State  ('new_activity_date',        'value'   ),
     State  ('new_activity_days',        'value'   ),
     State  ('new_activity_context',     'value'   ),
     State  ('new_activity_role',        'value'   ),
     State  ('new_activity_waypoints',   'value'   ),
     State  ('new_activity_participants','value'   ),
     State  ('new_activity_topo',        'value'   ),
     State  ('new_activity_comment',     'value'   ), 
     State  ('activities_store',         'data'    ),
     State  ('activities_tabulator',     'multiRowsClicked')],
    prevent_initial_call=True
)
def save_new_activity(
    save_clicks, 
    label, cat, grade, start_date, days, context, role, waypoints, participants, topo, comments, activities_store, selected_activity
):

    hide_alert = True
    
    entry = {
        'label'       : label, 
        'category'    : cat,
        'grade'       : grade,
        'date'        : start_date,
        'days'        : days,
        'context'     : context,
        'role'        : role,
        'waypoints'   : ', '.join(waypoints),
        'participants': participants,
        'topo'        : topo,
        'comments'    : comments
        }

    # When saving a new activity
    if selected_activity == []:
        id = activities_store['id'].max() + 1

    # when saving changes to an existing activity
    else:
        id = selected_activity[0]['id']

    activities_store[id] = entry
    
    # Save to local file
    activities_df = utilities.activities_dict_to_df(activities_store)
    activities_df = activities_df.reset_index()[['id', 'label', 'category', 'grade', 'date', 'days', 'context', 'role', 'waypoints', 'participants', 'topo', 'comments']]
    activities_df.to_json('data_activities.json', orient='table', index=False)

    return (
        hide_alert,
        activities_store
    )


# Update Map & figure when filters are updated
#----------------------------------------------------------------------------
@app.callback( 
    [Output('place_map',                 'figure'  ),
     Output('places_plot',               'figure'  ),
     Output('activities_plot',           'figure'  ),
     Output('summits_total',             'children'),
     Output('passes_total',              'children'),
     Output('huts_total',                'children'),
     Output('activities_tabulator',      'data'    ),
     Output('grades_overtime',           'children'),
     Output('context_overtime',          'figure'  ),
     Output('search_place',              'data'    ),
     Output('places_trivia_tabulator',   'data'    ),
     Output('places_plot_div',           'style'   ),
     Output('places_trivia_div',         'style'   )],
    [Input ('altitude_slider',           'value'   ),
     Input ('category_selection',        'value'   ),
     Input ('search_place',              'value'   ),
     Input ('places_plot_switch',        'value'   ),
     Input ('cumulative_activities',     'checked' ),
     Input ('places_store',              'data'    ),
     Input ('activities_store',          'data'    ),
     Input ('filter_activity_waypoints', 'value'   ),
     Input ('language',                  'children')],
    [State ('altitude_slider',           'min'     ),
     State ('altitude_slider',           'max'     )]
)
def update_all(
    altitude_values, categories, search_place, places_plot_switch, cumulative_activities, places_store, activity_store, filter_waypoint, language,
    min_alt, max_alt
):

    places_trivia_tabulator = []
    places_figure = None
    activities_figure = None
    grades_overtime_layout=  None
    context_overtime = None
    places_plot_div   = {'display': 'none'}
    places_trivia_div = {'display': 'none'}

    if len(places_store)==0 or len(activity_store)==0:
        return (None, None, None, 0, 0, 0, [], None, None, [])

    places = utilities.places_dict_to_df(places_store)
    stats_places = places.groupby('category')['category'].count()

    activities = utilities.activities_dict_to_df(activity_store).sort_values(by='date', ascending=False)
    
    # Translate categorical variables
    categories_map = utilities.translation['activities']
    categories_map = {key: categories_map[key][language] for key in categories_map }
    activities['category_translated'] = activities['category'].map(categories_map)
    context_map = utilities.translation['contexts']
    context_map = {key: context_map[key][language] for key in context_map }
    activities['context_translated'] = activities['context'].map(context_map)
    role_map = utilities.translation['roles']
    role_map = {key: role_map[key][language] for key in role_map }
    activities['role_translated'] = activities['role'].map(role_map)

    category_map = utilities.translation['places']
    category_map = {key: category_map[key][language] for key in category_map }
    places['category_translated'] = places['category'].map(category_map)

    if filter_waypoint:
        activities = activities[activities['waypoints'].str.contains(filter_waypoint, regex=False, na=False)]


    if places_plot_switch == 'trivia':
        
        places_trivia_div = {}
    
        # Trivia
        places = places[places['category'].isin(['pass', 'hut', 'summit'])]

        min_alt = places.loc[places.groupby('category_translated').altitude.idxmin()]
        min_alt['lowest'] = min_alt['waypoint'] + ' (' + min_alt['altitude'].astype(str) + ' m)'
        min_alt = min_alt[['category_translated', 'lowest']]

        max_alt = places.loc[places.groupby('category_translated').altitude.idxmax()]
        max_alt['highest'] = max_alt['waypoint'] + ' (' + max_alt['altitude'].astype(str)  + ' m)'
        max_alt = max_alt[['category_translated', 'highest']]
  
        waypoints = activities['waypoints']
        most_visited = []
        for waypoint in waypoints:
            if waypoint:
                for w in waypoint.split(', '):
                    most_visited.append(w)
        
        most_visited = pd.DataFrame(most_visited, columns=['waypoint'])
        most_visited = most_visited.merge(places[['waypoint', 'category']], on='waypoint', how='left')
        
        category_map = utilities.translation['places']
        category_map = {key: category_map[key][language] for key in category_map }
        most_visited['category_translated'] = most_visited['category'].map(category_map)
        
        most_visited = most_visited.groupby(['category_translated', 'waypoint']).count().reset_index()
        most_visited = most_visited.loc[most_visited.groupby('category_translated').category.idxmax()]
        most_visited['most_visited'] = most_visited['waypoint'] + ' (' + most_visited['category'].astype(str) + ')'

        places_trivia_tabulator = reduce(
            lambda  left,right: pd.merge(left,right,on=['category_translated'], how='outer'), [min_alt, max_alt, most_visited]
        )
        places_trivia_tabulator = places_trivia_tabulator.to_dict('records')

    else: 

        places_plot_div   = {}    

        # Places plot
        places_figures = {
            'curve'        : utilities.waypoints_by_altitude(places, (min_alt, max_alt), categories, language),
            'exploded_view': utilities.waypoints_by_year(places, activities, (min_alt, max_alt), categories, language),
            'year_summary' : utilities.places_yearly_summary(places, activities, language)
        }

        places_figure = places_figures[places_plot_switch]

        # Activities plot
        activities_figure = utilities.activities_yearly_summary(activities, cumulative_activities, language)

        # Grades plot
        grades_overtime = utilities.grades_overtime(activities, language)
        grades_overtime_layout = html.Div(
            dbc.Row(
                [
                    dbc.Col([
                        dcc.Graph(figure=grades_overtime[key])
                    ], width=6)
                for key in grades_overtime]
            )
        )

        # Contexts plot
        context_overtime = utilities.contexts_yearly_summary(activities, language)      
   

    # Main map
    if search_place:
        search_place = [search_place]

    map_figure = utilities.create_map(
        places,
        language,
        search_place, 
        800,
        altitude_values,
        (min_alt, max_alt), 
        categories,
    )

    all_places = places['waypoint'].unique()
    all_places.sort()

    return (
        map_figure,
        places_figure,
        activities_figure,
        stats_places['summit'],
        stats_places['pass'],
        stats_places['hut'],
        activities.to_dict('records'),
        grades_overtime_layout,
        context_overtime, 
        all_places,
        places_trivia_tabulator,
        places_plot_div,
        places_trivia_div
    )

#----------------------------------------------------------------------------
# @app.callback(
#     Output('test',           'children'    ),
#     [Input('activities_plot', 'clickData'),
#      Input('places_plot', 'clickData')],
     
# )
# def tets(click1, click2):

#     print(click1)
#     print(click2)
#     return ''



# Display how many activities/days were selected
#----------------------------------------------------------------------------
@app.callback(
    [Output('activities_total',    'children'    ),
     Output('days_total',          'children'    )],
     Input('activities_tabulator', 'dataFiltered')
)
def filter_activities(rows):

    n = sum([1 for row in rows['rows'] if row != None])    
    days = sum([row['days'] for row in rows['rows'] if row != None])    

    return (
        n,
        math.ceil(days)
    )


# Display filters
#----------------------------------------------------------------------------
@app.callback(
    Output('collapse_map_filter',  'is_open' ),
    Input ('filter_map',           'n_clicks'),
    State ('collapse_map_filter',  'is_open' ),
    prevent_initial_call=True
)
def collapse_map_filter(n, is_open):
    return not(is_open)


@app.callback(
    Output('collapse_activities_filter', 'is_open' ),
    Input ('filter_activities',          'n_clicks'),
    State ('collapse_activities_filter', 'is_open' ),
    prevent_initial_call=True
)
def collapse_activities_filter(n, is_open):
    return not(is_open)


# Switch language
#----------------------------------------------------------------------------
@app.callback(
    [Output("navigation_segments",  "data"                  ),
     Output("filter_map",           "children"              ),
     Output("filter_activities",    "children"              ),
     Output("activities_tabulator", "columns"               ),
     Output("stats_segments",       "data"                  ),
     Output("language_fr",          "variant"               ),
     Output("language_en",          "variant"               ),
     Output("days_total_text",      "children"              ),
     Output("activities_total_text","children"              ),
     Output("summits_total_text",   "children"              ),
     Output("passes_total_text",    "children"              ),
     Output("huts_total_text",      "children"              ),
     Output("add_new_place",        "children"              ),
     Output("language",             "children"              ),
     Output("new_activity",         "children"              ),
     Output("places_plot_switch",   "children"              )],
    [Input("language_fr",           "n_clicks"              ),
     Input("language_en",           "n_clicks"              )],
)
def switch_language(french_click, english_click):

    translations = utilities.translation

    if ctx.triggered_id:
        language = ctx.triggered_id.split('_')[1]
    else: 
        language = 'fr'

    if language=='fr':
        variant_fr='outline'
        variant_en='light'
    elif language=='en':
        variant_en='outline'
        variant_fr='light'
   
    navigation_segments = [ {'value':item['name'], 'label': item[language]} for item in translations['navigation_segments']]
    
    filter_map_button = translations['filter_buttons'][language]
    filter_activities_button = translations['filter_buttons'][language]
    
    activities_tabulator_columns = [
        {"formatter": "rowSelection", "titleFormatter": "rowSelection", "hozAlign": "center", "headerSort": "false", 'width':50}, 
        {'field'       : 'id', 'title': 'id', 'visible':False}
    ] + [
        {'field'       : item['name'],
         'title'       : item[language],
         'headerFilter': True,
         'hozAlign'    : 'left',
        }
        for item in translations['activities_tabulator_columns']
    ]

    stats_segments = [ {'value':item['name'], 'label': item[language]} for item in translations['stats_segments']]

    days_total_text       = translations['days_total_text'][language]
    activities_total_text = translations['activities_total_text'][language]
    summits_total_text    = translations['summits_total_text'][language]
    passes_total_text     = translations['passes_total_text'][language]
    huts_total_text       = translations['huts_total_text'][language]
    add_new_place         = translations['add_new_place'][language]
    new_activity          = translations['add_new_activity'][language]

    places_plot_switch = [
        dmc.Radio(
        translations['groupby'][groupby][language], value=groupby)
        for groupby in ['exploded_view', 'year_summary', 'curve', 'trivia']
    ]

    return (
        navigation_segments,
        filter_map_button,
        filter_activities_button,
        activities_tabulator_columns,
        stats_segments, 
        variant_fr,
        variant_en,
        days_total_text,
        activities_total_text,
        summits_total_text,
        passes_total_text,
        huts_total_text,
        add_new_place,
        language,
        new_activity,
        places_plot_switch
    )
from dash import Input, Output, State, ctx, dcc
from dash import html
from app_init import app
import utilities
import pandas as pd
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import dash_bootstrap_components as dbc


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
        layout_context
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
     Output('selected_activity_icon',      'icon'            ),
    # Output('small_map',                   'figure'          )
    ],
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
        table_width = 12
        details_width = 0
        div_style = {'display': 'none'}
        days = None
        href = None
        link_label = None
        comments = None
        grade = None
        waypoints = None
        activity_icon = "mdi:ski" # it needs a default value...
        map_figure = None
   
    else: 
        table_width = 6
        details_width = 6
        div_style = {}
        
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
            places = pd.DataFrame(places_store)
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

        #map_figure = utilities.create_map(places, height=200)

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
       # map_figure
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
    prevent_initial_call=True
)
def enable_save_new_place(
    name, lat, lon, alt, cat
):

    return (name=='' or lat=='' or lon=='' or alt=='' or cat==None)


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
     Input ('save_new_place',        'n_clicks'),
    [State ('new_place_name',        'value'   ),
     State ('new_place_latitude',    'value'   ),
     State ('new_place_longitude',   'value'   ),
     State ('new_place_altitude',    'value'   ),
     State ('new_place_category',    'value'   ),
     State ('places_store',          'data'    )],
    prevent_initial_call=True
)
def save_new_place(
    clicks, 
    name, lat, lon, alt, cat, places_store

):

    # Load current data and add new one
    places = pd.concat([
        pd.DataFrame(places_store)[['waypoint', 'latitude','longitude', 'altitude', 'category']], 
        pd.DataFrame([
            {'waypoint': name, 'latitude': lat, 'longitude': lon, 'altitude': alt, 'category': cat}
        ])
    ]).reset_index()[['waypoint', 'latitude','longitude', 'altitude', 'category']]

    # Save to local file
    places.to_json('places.json', orient='table', index=False)

    # for dropdown
    places_data = places['waypoint'].unique()
    places_data.sort()

    return (
        False,
        '',
        '',
        '',
        '',
        None,
        places.to_dict('records'),
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
     State  ('activities_tabulator',     'multiRowsClicked')],
    prevent_initial_call=True
)
def save_new_place(
    new_clicks, edit_clicks,
    label, cat, grade, start_date, days, context, role, waypoints, participants, topo, comments, selected_activity
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

    # Edit: load values in the field
    elif ctx.triggered_id == 'edit_activity':

        modal_title = 'Edit this activity'
        label       = selected_activity[0]['label']
        cat         = selected_activity[0]['category']
        grade       = selected_activity[0]['grade']
        start_date  = selected_activity[0]['date']
        days        = selected_activity[0]['days']
        context     = selected_activity[0]['context']
        role        = selected_activity[0]['role']
        try: 
            waypoints   = selected_activity[0]['waypoints'].split(', ')
        except: # handle my dirty legacy data
            waypoints = []
        topo        = selected_activity[0]['topo']
        comments    = selected_activity[0]['comments']
        participants = selected_activity[0]['participants']

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
def save_new_place(
    save_clicks, 
    label, cat, grade, start_date, days, context, role, waypoints, participants, topo, comments, activities_store, selected_activity
):

    hide_alert = True
    activities = pd.DataFrame(activities_store)
    entry =  pd.DataFrame([
        {'label'      : label, 
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
    ])

    # save a new activity
    if selected_activity == []:
        activities = pd.concat([activities, entry])

    # save changes to an existing activity
    else:
        activities.set_index(['label', 'date'], inplace=True)
        entry.set_index(['label', 'date'], inplace=True)
        activities.update(entry)

    activities = activities.reset_index()[['label', 'category', 'grade', 'date', 'days', 'context', 'role', 'waypoints', 'participants', 'topo', 'comments']]

    # Save to local file
    activities.to_json('activities.json', orient='table', index=False)

    return (
        hide_alert,
        activities.to_dict('records'),
    )



# Update Map & figure when filters are updated
#----------------------------------------------------------------------------
@app.callback( 
    [Output('place_map',                 'figure'  ),
     Output('all_waypoints',             'figure'  ),
     Output('summits_total',             'children'),
     Output('passes_total',              'children'),
     Output('huts_total',                'children'),
     Output('activities_tabulator',      'data'    ),
     Output('grades_overtime',           'children'),
     Output('context_overtime',          'figure'  )],
    [Input ('altitude_slider',           'value'   ),
     Input ('year_slider',               'value'   ),                
     Input ('category_selection',        'value'   ),
     Input ('search_place',              'value'   ),
     Input ('switch_waypoints_fig',      'value'   ),
     Input ('places_store',              'data'    ),
     Input ('activities_store',          'data'    ),
     Input ('filter_activity_waypoints', 'value'   ),
     Input ('language',                  'children')],
    [State ('altitude_slider',           'min'     ),
     State ('altitude_slider',           'max'     ), 
     State ('year_slider',               'min'     ),
     State ('year_slider',               'max'     ),
     State ('metadata_store',            'data'    )]
)
def update_all(
    altitude_values, year_values, categories, search_place, switch, places_store, activity_store, filter_waypoint, language,
    min_alt, max_alt, min_year, max_year, metadata_store
):

    if len(places_store)==0 or len(activity_store)==0:
        return (None,
        None,
        0,
        0,
        0,
        []
        )

    places = pd.DataFrame(places_store)
    stats_places = places.groupby('category')['category'].count()

    activities = pd.DataFrame(activity_store).sort_values(by='date', ascending=False)
    activities = utilities.massage_activity_data(activities, metadata_store['activity'])
    
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

    if switch == 'altitude':
        all_waypoints_figure = utilities.waypoints_by_altitude(places, (min_alt, max_alt), categories, language)

    elif switch == 'year':
        all_waypoints_figure = utilities.waypoints_by_year(places, activities, (min_alt, max_alt), categories, language)

    if search_place:
        search_place = [search_place]

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

    context_overtime = utilities.figure_context_evolution(activities, language)

    map_figure = utilities.create_map(
        places,
        language,
        search_place, 
        800,
        altitude_values,
        (min_alt, max_alt), 
        year_values,
        (min_year, max_year),
        categories,
    )

    return (
        map_figure,
        all_waypoints_figure,
        stats_places['summit'],
        stats_places['pass'],
        stats_places['hut'],
        activities.to_dict('records'),
        grades_overtime_layout,
        context_overtime
    )


# Update Year stats figures on switch
#----------------------------------------------------------------------------
@app.callback(
     Output('year_stats_figure', 'figure'  ),
     Input ('switch_year_stats', 'value'   ),
    [State ('activities_store',  'data'    ),
     State ('places_store',      'data'    ),
     State ('language',          'children')],
)
def update_year_figure(
    switch,
    activity_store, places_store, language
):
    
    activities = pd.DataFrame(activity_store)
    places = pd.DataFrame(places_store)

    categories_map = utilities.translation['activities']
    categories_map = {key: categories_map[key][language] for key in categories_map }
    activities['category_translated'] = activities['category'].map(categories_map)

    category_map = utilities.translation['places']
    category_map = {key: category_map[key][language] for key in category_map }
    places['category_translated'] = places['category'].map(category_map)

    if switch == 'activity':
        figure = utilities.figure_activities_overtime(activities, language)

    elif switch=='places':
        figure = utilities.figure_waypoints_overtime(places, activities, language)

    return figure


# Display how many activities/days were selected
#----------------------------------------------------------------------------
@app.callback(
    [Output('activities_total',    'children'    ),
     Output('days_total',          'children'    )],
     Input('activities_tabulator', 'dataFiltered')
)
def filterering_tabilator(rows):

    n = sum([1 for row in rows['rows'] if row != None])    
    days = sum([row['days'] for row in rows['rows'] if row != None])    

    return (
        n,
        int(days)
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
     Output("new_activity",         "children"              )],
    [Input("language_fr",           "n_clicks"              ),
     Input("language_en",           "n_clicks"              )],
)
def switch_language(french_click, english_click):

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
   
    navigation_segments = [ {'value':item['name'], 'label': item[language]} for item in utilities.translation['navigation_segments']]
    
    filter_map_button = utilities.translation['filter_buttons'][language]
    filter_activities_button = utilities.translation['filter_buttons'][language]
    
    activities_tabulator_columns = [
        {"formatter": "rowSelection", "titleFormatter": "rowSelection", "hozAlign": "center", "headerSort": "false", 'width':50}, 
    ] + [
        {'field'       : item['name'],
         'title'       : item[language],
         'headerFilter': True,
         'hozAlign'    : 'left',
        }
        for item in utilities.translation['activities_tabulator_columns']
    ]

    stats_segments = [ {'value':item['name'], 'label': item[language]} for item in utilities.translation['stats_segments']]

    days_total_text = utilities.translation['days_total_text'][language]
    activities_total_text = utilities.translation['activities_total_text'][language]
    summits_total_text = utilities.translation['summits_total_text'][language]
    passes_total_text = utilities.translation['passes_total_text'][language]
    huts_total_text = utilities.translation['huts_total_text'][language]

    add_new_place = utilities.translation['add_new_place'][language]

    new_activity = utilities.translation['add_new_activity'][language]

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
        new_activity
    )
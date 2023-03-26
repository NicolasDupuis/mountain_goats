import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import yaml
import utilities


#------------------------------------------------------------------------------------------------
def import_colors(
    scope   : str,
    language: str,
) -> dict:

    with open('data/color_settings.yaml') as file:
        colors_settings = yaml.load(file, Loader=yaml.FullLoader)

    translation = utilities.translation[scope]

    return {translation[key][language]: colors_settings[scope][key] for key in colors_settings[scope]}


#------------------------------------------------------------------------------------------------------------
def get_waypoints_overtime(
    places    : pd.DataFrame,
    activities: pd.DataFrame,
    language  :str
) -> pd.DataFrame:
    '''
    Merge Places and Activities to get waypoints per time period
    '''

    df = activities[['date', 'waypoints']].dropna().rename(columns={'waypoints': 'waypoint'})
    df1 = pd.DataFrame(df['waypoint'].str.split(', ').tolist(), index=df['date']).stack()
    df1 = df1.reset_index([0, 'date'])
    df1.columns = ['date', 'waypoint']
    df1['year'] = df1['date'].str.split('-').str[0].astype(int)

    activity_year = df1.merge(
        places[['waypoint', 'category', 'category_translated', 'altitude', 'latitude', 'longitude']],
        how = 'left',
        on  = 'waypoint'
    ).dropna()

    return activity_year


#------------------------------------------------------------------------------------------------
def figure_activities_overtime(
    activities: pd.DataFrame,
    language  : str
) -> go.Figure:
    '''
    Days in the mountain, over time and by activity category
    '''    

    if len(activities) == 0:
        return go.Figure()

    colors = import_colors('activities', language)
    df = pd.DataFrame(activities.groupby(['year', 'category_translated'])['days'].sum()).reset_index()

    df['year'] = df['year'].astype(int)

    activities_overtime = go.Figure(
        data = [go.Bar(
            name         = activity,
            x            = list(df[df['category_translated'] == activity]['year']),
            y            = list(df[df['category_translated'] == activity]['days']),
            marker_color = colors[activity])
    
            for activity in df['category_translated'].unique()
        ]
    )

    activities_overtime.update_layout(
        barmode = 'stack',
        height  = 600,
        yaxis   = dict(title='days')
    )

    df = activities.groupby(['year'])['days'].sum()

    for year, days in df.items():

        activities_overtime.add_annotation(
            x         = year,
            y         = days+3,
            text      = days,
            showarrow = False
        )

    return activities_overtime


#------------------------------------------------------------------------------------------------
def figure_waypoints_overtime(
    places    : pd.DataFrame,
    activities: pd.DataFrame,
    language  : str
) -> go.Figure:
    '''
    Waypoints in the mountain, over time and by category
    '''
     
    colors = import_colors('places', language)
    waypoints_overtime = get_waypoints_overtime(places, activities, language)
    waypoints_overtime = pd.DataFrame(waypoints_overtime.groupby(['year', 'category_translated'])['waypoint'].count()).reset_index()

    waypoints_overtime_fig = go.Figure(
        data = [go.Bar
            (name        = category,
             x           = list(waypoints_overtime[waypoints_overtime['category_translated'] == category]['year']),
             y           = list(waypoints_overtime[waypoints_overtime['category_translated'] == category]['waypoint']),
             marker_color = colors[category])
                
            for category in waypoints_overtime['category_translated'].unique()
        ]
    )                  
        
    waypoints_overtime_fig.update_layout(barmode='stack')
    waypoints_overtime_fig.update_layout(yaxis=dict(title='Lieux'))

    return waypoints_overtime_fig


#------------------------------------------------------------------------------------------------
def figure_context_evolution(
    activities: pd.DataFrame,
    language : str
) -> go.Figure:
    '''
    Create context evolution plot
    '''

    if len(activities) == 0:
        return go.Figure()


    context_map = utilities.translation['contexts']
    context_map = {key: context_map[key][language] for key in context_map }
    activities['context'] = activities['context'].map(context_map)
    activities['year'] = activities['year'].astype(int)

    role_map = utilities.translation['roles']
    role_map = {key: role_map[key][language] for key in role_map }

    activities['role'] = activities['role'].map(role_map)
    activities['role'].fillna('?', inplace=True)

    df = pd.DataFrame(activities.groupby(['year', 'context', 'role' ])['days'].sum()).reset_index()

    context_fig = px.bar(
        df,
        x         = 'year',
        y         = 'days',
        color     = 'role',
        facet_col = 'context'
    )

    context_fig.update_layout(
        yaxis     = dict(title='days'),
        legend_title = ''
    )
    
    context_fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    return context_fig


#------------------------------------------------------------------------------------------------
def grades_overtime(
    activities : pd.DataFrame, 
    language   : str
) -> go.Figure:
    '''
    Activities by grades, overtime
    '''

    climb_by_grades = {}
    colors = import_colors('activities', language)

    activities = activities[activities['grade'] !='Piste']

    for activity in colors.keys():

        df = activities[activities['category_translated']==activity].sort_values(by='grade_num')
        
        fig = go.Figure(
            data = go.Scatter(
                x            = df['date'],
                y            = df['grade'],
                mode         = 'markers',
                marker_color = colors[activity],
                text         = df['label']
            )
        )

        total = df.groupby('grade').count()
        for idx, row in total.iterrows():
            fig.add_annotation(x=max(df['date']), y=idx, text=f"({row['days']})", showarrow=False, xshift=30 )

        fig.update_layout(title=f'{activity} (' + str(len(df)) + ')')
        climb_by_grades[activity] = fig

    return climb_by_grades
        

#------------------------------------------------------------------------------------------------
def waypoints_by_altitude(
    places: pd.DataFrame,
    altitude_range,
    categories, 
    language
):

    colors = import_colors('places', language)

    # Apply user's filter on places 
    df = places[
        (places['altitude'] >= altitude_range[0]) &
        (places['altitude'] <= altitude_range[1]) & 
        (places['category'].isin(categories))
    ]

    # Stats
    df = df.sort_values('altitude').reset_index()
    df['index'] = df.index

    fig = go.Figure(
        data = [go.Scatter(
            name         = category,
            x            = df[df['category_translated']==category]['index'],
            y            = df[df['category_translated']==category]['altitude'],
            mode         = 'markers',
            text         = df[df['category_translated']==category]['waypoint'],
            marker_color = colors[category])

            for category in df['category_translated'].unique()
        ]
    )                            

    fig.update_layout(yaxis=dict(title='Altitude'))
    fig.update_xaxes(showticklabels=False)  

    return fig


#------------------------------------------------------------------------------------------------
def waypoints_by_year(
    places         : pd.DataFrame,
    activities     : pd.DataFrame,
    altitude_range : list,
    categories     : list,
    language       : str
) -> go.Figure:

    waypoints_overtime = get_waypoints_overtime(places, activities, language)
    colors = import_colors('places', language)

    filtered_places = waypoints_overtime[
        (waypoints_overtime['altitude'] >= altitude_range[0]) &
        (waypoints_overtime['altitude'] <= altitude_range[1]) & 
        (waypoints_overtime['category'].isin(categories))
    ]
    
    figure = go.Figure(
        data = [ go.Scatter(
            name         = category,
            x            = filtered_places[filtered_places['category_translated']==category]['date'],
            y            = filtered_places[filtered_places['category_translated']==category]['altitude'],
            mode         = 'markers',
            text         = filtered_places[filtered_places['category_translated']==category]['waypoint'],
            marker_color = colors[category])

            for category in filtered_places['category_translated'].unique()
        ]
    )

    figure.update_layout(
        yaxis    = dict(title='Altitude'),
        autosize = False,
        height   = 800)

    return figure


#------------------------------------------------------------------------------------------------------------
def create_map(
    all_places      : pd.DataFrame,
    language        : str,
    search_place    = None,
    height          = 800,
    altitude_values = None,
    altitude_range  = None,
    year_values     = None,
    year_range      = None,
    categories      = None,
    zoom            = 8,    
) -> px.scatter_mapbox:

    # User searched for that place, let's focus on it
    if search_place:

        all_places = all_places[all_places['waypoint'].isin(search_place)]
        
        if len(all_places) == 1:
            zoom = 12

    # Filter on places category?
    if categories: 
        all_places = all_places[all_places['category'].isin(categories)]

    # Filter on altitude?
    if altitude_values and altitude_range:
        if altitude_range != altitude_values:
            all_places = all_places[ all_places['altitude'].between(altitude_values[0], altitude_values[1], inclusive='both')]

    # Filter on year?
    # if year_range and year_values:
    #     if year_values != year_range:
    #         places = figures.activity_year[figures.places['category'].isin(categories)]
    #         places = places[ places['date'].between(datetime(year_values[0], 1, 1),
    #                                                 datetime(year_values[1] - 1, 12, 31),
    #                                                 inclusive='both')]

    waypoint_category_colors = import_colors('places', language)
    
    map_figure = px.scatter_mapbox(
        all_places,
        lat                     = "latitude", 
        lon                     = "longitude",
        color                   = 'category_translated',
        color_discrete_map      = {category: waypoint_category_colors[category] for category in waypoint_category_colors},
        hover_name              = "waypoint",
        hover_data              = ['altitude'],
        zoom                    = zoom,
        height                  = height
    )

    try: 
        mapbox_token = open(".mapbox_token").read()
        map_figure.update_layout(mapbox_style='outdoors', mapbox_accesstoken=mapbox_token)
    except:
        pass


    map_figure.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        legend_title = "",
    )

    return map_figure
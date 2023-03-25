import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import yaml


#------------------------------------------------------------------------------------------------
def import_colors():

    with open('data/color_settings.yaml') as file:
        colors = yaml.load(file, Loader=yaml.FullLoader)
    
    return colors


#------------------------------------------------------------------------------------------------------------
def get_waypoints_overtime(
    places    : pd.DataFrame,
    activities: pd.DataFrame
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
        places[['waypoint', 'category', 'altitude', 'latitude', 'longitude']],
        how = 'left',
        on  = 'waypoint'
    ).dropna()

    return activity_year


#------------------------------------------------------------------------------------------------
def figure_activities_overtime(
    activities: pd.DataFrame
) -> go.Figure:
    '''
    Days in the mountain, over time and by activity category
    '''    

    if len(activities) == 0:
        return go.Figure()

    colors = import_colors()

    df = pd.DataFrame(activities.groupby(['year', 'category'])['days'].sum()).reset_index()

    activities_overtime = go.Figure(
        data = [go.Bar(
            name         = activity,
            x            = list(df[df['category'] == activity]['year']),
            y            = list(df[df['category'] == activity]['days']),
            marker_color = colors['activity_category_color'][activity])
    
            for activity in df['category'].unique()
        ]
    )

    activities_overtime.update_layout(barmode='stack')
    activities_overtime.update_layout(yaxis=dict(title='days'))

    df = activities.groupby(['year'])['days'].sum()
    for year, days in df.items():
        activities_overtime.add_annotation(x=year, y=days+3, text=f"{days}", showarrow=False)

    return activities_overtime


#------------------------------------------------------------------------------------------------
def figure_waypoints_overtime(
    places    : pd.DataFrame,
    activities: pd.DataFrame
):
    '''
    Waypoints in the mountain, over time and by category
    '''
     
    colors = import_colors()

    waypoints_overtime = get_waypoints_overtime(places, activities)

    waypoints_overtime = pd.DataFrame(waypoints_overtime.groupby(['year', 'category'])['waypoint'].count()).reset_index()

    waypoints_overtime_fig = go.Figure(
        data = [go.Bar
            (name        = category,
             x           = list(waypoints_overtime[waypoints_overtime['category'] == category]['year']),
             y           = list(waypoints_overtime[waypoints_overtime['category'] == category]['waypoint']),
             marker_color = colors['waypoint_category_color'][category])
                
            for category in waypoints_overtime['category'].unique()
        ]
    )                  
        
    waypoints_overtime_fig.update_layout(barmode='stack')
    waypoints_overtime_fig.update_layout(yaxis=dict(title='Lieux'))

    return waypoints_overtime_fig


#------------------------------------------------------------------------------------------------
def figure_context_evolution(
    activities: pd.DataFrame
) -> go.Figure:
    '''
    Create context evolution plot
    '''

    if len(activities) == 0:
        return go.Figure()

    def context(row):

        if 'with_guide' in row['context'] or row['role'] in ['second', 'participant']:
            return 'Encadré & Second' 
        elif row['role'] in ['lead', 'first']:
            return 'Encadrant & Premier' 
        elif row['role'] in ['switch']:
            return 'Réversible' 
        else:
            return 'Solo & N/A'

    activities.fillna('', inplace=True)
    activities['Situation'] = activities.apply(context, axis=1)
    df = pd.DataFrame(activities.groupby(['year', 'Situation'])['days'].sum()).reset_index()

    context_fig = go.Figure(
        data=[  go.Bar(  name='Solo & N/A',
                        x=list(df[df['Situation']=='Solo & N/A']['year']),
                        y=list(df[df['Situation']=='Solo & N/A']['days']),
                        marker_color='blue'),
                go.Bar(  name='Encadré & Second',
                        x=list(df[df['Situation']=='Encadré & Second']['year']),
                        y=list(df[df['Situation']=='Encadré & Second']['days']),
                            marker_color='orangered'),                            
                go.Bar(  name='Réversible',
                        x=list(df[df['Situation']=='Réversible']['year']),
                        y=list(df[df['Situation']=='Réversible']['days']),
                        marker_color='darkorchid'),
                go.Bar(  name='Encadrant & Premier',
                        x=list(df[df['Situation']=='Encadrant & Premier']['year']),
                        y=list(df[df['Situation']=='Encadrant & Premier']['days']),
                        marker_color='forestgreen'),       
        ])

    context_fig.update_layout(barmode='stack')
    context_fig.update_layout(yaxis=dict(title='days'))

    return context_fig


#------------------------------------------------------------------------------------------------
def figure_climb_by_grades(activities):
    '''
    Activities by grades
    '''

    climb_by_grades = {}
    colors = import_colors()

    for activity in ['mountaineering', 'hike', 'climbing', 'ski']:

        if activity == 'ski': 
            df = activities[
                (activities['category'] == activity) & 
                (activities['grade']    != 'Piste' )
            ]

        else: 
            df = activities[activities['category']==activity]
        
        df = df.sort_values(by='grade')
        fig = go.Figure(
            data = go.Scatter(
                        x            = df['date'],
                        y            = df['grade'],
                        mode         = 'markers',
                        marker_color = colors['activity_category_color'][activity],
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
def update_waypoints_figure(
    places: pd.DataFrame,
    altitude_range,
    categories
):

    colors = import_colors()

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
            x            = df[df['category']==category]['index'],
            y            = df[df['category']==category]['altitude'],
            mode         = 'markers',
            text         = df[df['category']==category]['waypoint'],
            marker_color = colors['waypoint_category_color'][category])

            for category in df['category'].unique()
        ]
    )                            

    fig.update_layout(yaxis=dict(title='Altitude'))
    fig.update_xaxes(showticklabels=False)  

    return fig


#------------------------------------------------------------------------------------------------
def update_waypoints_year_figure(
    places,
    activities,
    altitude_range,
    categories
):

    waypoints_overtime = get_waypoints_overtime(places, activities)
    colors = import_colors()    

    filtered_places = waypoints_overtime[
        (waypoints_overtime['altitude'] >= altitude_range[0]) &
        (waypoints_overtime['altitude'] <= altitude_range[1]) & 
        (waypoints_overtime['category'].isin(categories))
    ]
    
    figure = go.Figure(
        data = [ go.Scatter(
            name         = category,
            x            = filtered_places[filtered_places['category']==category]['date'],
            y            = filtered_places[filtered_places['category']==category]['altitude'],
            mode         = 'markers',
            text         = filtered_places[filtered_places['category']==category]['waypoint'],
            marker_color = colors['waypoint_category_color'][category])

            for category in filtered_places['category'].unique()
        ]
    )

    figure.update_layout(yaxis=dict(title='Altitude'))

    figure.update_layout(
        autosize=False,
        height=800)

    return figure


#------------------------------------------------------------------------------------------------------------
def create_map(
    all_places      : pd.DataFrame,
    search_place    = None,
    height          = 800,
    altitude_values = None,
    altitude_range  = None,
    year_values     = None,
    year_range      = None,
    categories      = None,
    zoom            = 8
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

    waypoint_category_colors = import_colors()['waypoint_category_color']
    
    map_figure = px.scatter_mapbox(
        all_places,
        lat                     = "latitude", 
        lon                     = "longitude",
        color                   = 'category',
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

    map_figure.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    return map_figure
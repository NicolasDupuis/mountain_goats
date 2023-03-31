import pandas as pd
import utilities

#------------------------------------------------------------------------------------------------------------
def apply_numeric_grading(row, grades):

    activity = row['category']
    grade = row['grade']

    try: 
        return grades[activity]['grades'][grade]
    except:
        return grade


#------------------------------------------------------------------------------------------------------------
def load_data(
    metadata   : dict,
    activities = 'data_activities.json',
    places     = 'data_places.json',
) -> tuple: # of dicts
    '''
    Load Places and Activities from json files. Returns dicts.
    '''
    
    try: 
        places = pd.read_json(places, orient='table').set_index('waypoint').to_dict('index')
    except Exception as error:
        print('Error in load_data: ', repr(error))
        places = {}

    try:
        activities = pd.read_json(activities, orient='table')
        activities = utilities.massage_activity_data(activities, metadata['activity'])
        activities = activities.set_index('id').to_dict('index')

    except Exception as error:
        print('Error in load_data: ', repr(error))
        activities = {}

    return (
        places,
        activities
    )


#------------------------------------------------------------------------------------------------------------
def massage_activity_data(
    activities: pd.DataFrame,
    grades    : dict
) -> pd.DataFrame:

    activities['grade_num'] = activities.apply(apply_numeric_grading, grades=grades, axis=1)
    activities['date'] = activities['date'].astype('str')
    activities['year'] = activities['date'].str.split('-').str[0].astype(int)
    
    return activities

#------------------------------------------------------------------------------------------------------------
def places_dict_to_df(
    places: dict
) -> pd.DataFrame:
    
    return pd.DataFrame.from_dict(places, orient='index').reset_index().rename(columns={'index': 'waypoint'})

def activities_dict_to_df(
    activities: dict
) -> pd.DataFrame:
    
    return pd.DataFrame.from_dict(activities, orient='index').reset_index().rename(columns={'index': 'id'})

import pandas as pd

#------------------------------------------------------------------------------------------------------------
def apply_numeric_grading(row, grades):

    activity = row['category']
    grade = row['grade']

    try: 
        return grades[activity]['grades'][grade]
    except:
        return grade


#------------------------------------------------------------------------------------------------------------
def load_data():
    '''
    Load Places and Activities from json files. Create empty df if not available
    '''

    try: 
        places = pd.read_json('places.json',orient='table')
    except:
        places = pd.DataFrame(
            columns=['waypoint', 'latitude', 'longitude', 'altitude', 'category']
        )

    try:
        activities = pd.read_json('activities.json', orient='table').sort_values(by=['date'], ascending=[False])
    except:
        activities = pd.DataFrame(
            columns=['label', 'category', 'grade', 'date', 'days', 'context', 'role', 'waypoints', 'participants', 'topo', 'comments']
        )

    return places, activities


#------------------------------------------------------------------------------------------------------------
def massage_actitivy_data(activities, grades):

    activities['grade_num'] = activities.apply(apply_numeric_grading, grades=grades, axis=1)
    activities['date'] = activities['date'].astype('str')
    activities['year'] = activities['date'].str.split('-').str[0]
    
    return activities
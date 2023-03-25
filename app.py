'''
   Nicolas Dupuis, 2019-2023
'''

from datetime import datetime
from app_init import app
from dash_layouts import main_layout
import dash_callbacks
import os

local = os.path.exists('_local')

app.layout = main_layout(local)

if __name__ == '__main__':
    
   if local:
      print(f"Reload at {datetime.now()}")
      app.run_server(debug=True)

   else:
      app.run_server()
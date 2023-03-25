import dash
import dash_bootstrap_components as dbc

# ----------------------------------------------------------------------------
# Initialize the app
# ----------------------------------------------------------------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Mountain Goats"
server = app.server
app.config.suppress_callback_exceptions = True
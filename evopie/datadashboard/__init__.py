
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State

from flask import Flask
from flask.helpers import get_root_path
from flask_login import login_required


def register_dashapps(flask_server, title, base_pathname, layout, register_callbacks):
    from evopie.datadashboard import questionview, studentview

    # Meta tags for viewport responsiveness
    meta_viewport = {
        "name": "viewport",
        "content": "width=device-width, initial-scale=1, shrink-to-fit=no"}

    # Create the Dash applications    
    dashboardViewApp = dash.Dash(__name__,
                                 server=flask_server,
                                 url_base_pathname=f'/{base_pathname}',
                                 assets_folder=get_root_path(__name__) + '/../assets/',
                                 meta_tags=[meta_viewport])

    ## RPW:  The relative parent directory thing for assets_folder is a hack so
    ##       that I can keep this DashTesting application running the same whether
    ##       being driven by Dash or by Flask.  We'll have to figure out where we
    ##       want to host assets overall when we integrate.

    # Make sure their layouts and titles are configured.  We might need to modify
    # quesitonview and studentview so that their callback registration is inside
    # a function and therefore modular.
    with flask_server.app_context():
        # Setup the dashboard shell
        dashboardViewApp.title = title
        dashboardViewApp.layout = layout

        register_callbacks(dashboardViewApp)

    _protect_dashviews(dashboardViewApp)

def _protect_dashviews(dashapp):
    for view_func in dashapp.server.view_functions:
        if view_func.startswith(dashapp.config.url_base_pathname):
            dashapp.server.view_functions[view_func] = login_required(
                dashapp.server.view_functions[view_func])
            
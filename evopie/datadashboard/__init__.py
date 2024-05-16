
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State

from flask import Flask, redirect
from flask.helpers import get_root_path
from flask_login import login_required, current_user

# RPW:  Once the circular reference is resolved, change this to use dbaccess
from evopie.datadashboard.datalayer.dbvalidator import IsValidDashboardUser


def register_dashapps(flask_server):
    from evopie.datadashboard import questionview, studentview

    # Meta tags for viewport responsiveness
    meta_viewport = {
        "name": "viewport",
        "content": "width=device-width, initial-scale=1, shrink-to-fit=no"}

    # Create the Dash applications    
    dashboardViewApp = dash.Dash(__name__,
                                 server=flask_server,
                                 url_base_pathname='/datadashboard/',
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
        dashboardViewApp.title = "EvoPIE Data Dashboard"
        dashboardViewApp.layout = html.Div([ dcc.Location(id='url', refresh=False),
                                             html.Div(id='page-content') ])

        # Create the layouts and register the callbacks for the two views
        questionViewLayout = questionview.PopulateViewLayout()
        questionview.RegisterCallbacks(dashboardViewApp)

        studentViewAppLayout = studentview.PopulateViewLayout()
        studentview.RegisterCallbacks(dashboardViewApp)

        # Register the callback for the high-level URL response.
        # This returns the correct layout to populate the "page-content" of
        # the shell defined above
        @dashboardViewApp.callback(Output('page-content', 'children'),
                                   Input('url', 'pathname'))
        def display_main_view(pathname):
            print("DBG::: CALLBACK from dashboard shell!!  " + pathname)
            return select_page_layout(pathname, questionview.gLayout, studentview.gLayout)


def _protect_dashviews(dashapp):
    for view_func in dashapp.server.view_functions:
        if view_func.startswith(dashapp.config.url_base_pathname):
            dashapp.server.view_functions[view_func] = login_required(
                dashapp.server.view_functions[view_func])
            
            
# RPW:  This function should probably go away in favor of the "routes" used by
# EvoPIE once we fully integrate.  It's needed here until then so that
# Flask knows where to find the application
def select_page_layout(pathname, questionLayout, studentLayout):
    pathname = pathname.strip()
    last_url_field = pathname.strip("/").split("/")[-1].strip()
    print("DBG::: The user selected the path: " + pathname + " and the last field is: " + last_url_field)

    # If *just* the dashboard is loaded, assume we want the question view
    if (pathname == '/datadashboard/') and (last_url_field == "datadashboard"):
        last_url_field = "question"


    # Don't load any layout if we're not authenticated, try to redirect back to the main page?
    if (IsValidDashboardUser() < 0):
        redirectString = "The user is not authenticated or not an instructor.  The data dashboard is not accessible.  Redirecting to login page ..."
        redirectObject = html.Div(children=[
              html.Meta(httpEquiv="refresh", content="3; URL=/login"),
              html.H1(children="Acess Error", className="header"),
              html.P(children=redirectString, className="graph-component-message")] )
        return redirectObject
    
    elif (IsValidDashboardUser() == 0):
        redirectString = "The user is not an instructor or admin.  The data dashboard is not accessible.  Redirecting to main page ..."
        redirectObject = html.Div(children=[
              html.Meta(httpEquiv="refresh", content="3; URL=/"),
              html.H1(children="Acess Error", className="header"),
              html.P(children=redirectString, className="graph-component-message")] )
        return redirectObject

    # If we've asked to go back to the main
    elif (pathname == '/') and (last_url_field == ''):
        redirectString = "Returning to main page"
        redirectObject = html.Div(children=[html.P(children=redirectString, className="graph-component-message")] )        
    
    # If the URL request is for the question view, return that layout
    elif last_url_field == 'question':
        return questionLayout
    
    # If the URL request is for the student view, return that layout
    elif last_url_field == 'student':
        return studentLayout
    
    # If it's just for the dashboard, assume we want the question view by default
    elif (pathname == '') or (pathname == "datadashboard"):
        return questionLayout # for now "Analysis by Question" will be the entry point until we integrate with EvoPie
    
    # Anything else is a problem ... so return 404.  Probably this should be a valid HTML object, but hey ...
    else:
        return '404 Error' #html.p("404 Error:  The path " + pathname + " isn't a valid route")



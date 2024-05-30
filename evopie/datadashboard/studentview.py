## This is the "Analysis by Student" app. It will be missing a few visualizations such as heat maps since they will not provide novel information

# Deca, cluster, heatmap, traditonal, itemdiscrim 

from os import link
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import flask
import dash

import datetime

from evopie import APP
import evopie.datadashboard.utils as appUtils

import datalayer.dbaccess as da
import analysislayer.widgetbuilder as widgetbuilder
import analysislayer.utils as dataUtils


gWhichView = "StudentView"
gLayout = None
gQuizOptions = None

def PopulateViewLayout():
  """
  Build the HTML page layout for the question view.  Return the layout object, but also
  store on the global gLayout variable for this module.
  """
  global gLayout
  global gQuizOptions

  # Get the list of quizzes, and determine the default to use for the drop-down
  # If the quiz ID cookie is set, use that as the value for the drop down
  gQuizOptions = da.GetQuizOptionList()
  quizIDstr = appUtils.GetSelectedQuizIDCookie(gQuizOptions[0]['value'])

  # These are the fake dataframes will use until we integrate with EvoPIE
  APP.logger.info('')
  APP.logger.info('--' + __name__ + '-'.ljust(50, '-'))
  APP.logger.info("1.  Reinitializing, " + datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

  # Create the web page layout
  APP.logger.info("2.  Creating the layout")
  gLayout = html.Div(children=[
      
      # The drop-down quiz selector at the top
      html.Div(id="nav-topbar", className="rectangle", children=[
          html.Li(className="nav", children=[
              dcc.Link('Analysis by Question', href='/datadashboard/question/', className="nav-link"),
              dcc.Link('Analysis by Student', href='/datadashboard/student/', className="nav-link here"),
              dcc.Link('Back to EvoPIE', href='/', className="nav-link", refresh=True)
          ]),
          dcc.Dropdown(id="quizselect-dropdown-student", 
                      options= gQuizOptions,
                      persistence=True,
                      value=quizIDstr)]), 

      # The left-side navigation panel
      html.Div(id="nav-sidebar", className="rectangle", children=[
          # The title
          html.Div(id="titlebox", className="rectangle", children=[
            html.H3(children="EvoPIE Data Dashboard", id="evopie-title"),
          ]),

          # The left-side menu to select the analysis approach
          html.Div(id="menubox", className="rectangle", children=[
            dcc.Tabs(id="side-menu-student",
                    vertical=True,
                    persistence=True,
                    children=[
                        dcc.Tab(label="Dimension Extraction",      value="deca", className="menu-tab", id="menu-deca"),
                        dcc.Tab(label="Heat Map",                  value="hm",   className="menu-tab", id="menu-hm"),
                        dcc.Tab(label="Clustering",                value="mds",  className="menu-tab", id="menu-mds"),
                        dcc.Tab(label="Item Descrimination",       value="ids",  className="menu-tab", id="menu-ids"),
                        dcc.Tab(label="Traditional Difficulty",    value="trad", className="menu-tab", id="menu-trad"),
                ],),
          ]),

          html.Div(id="helpbox", className="rectangle", children=[
            dbc.Button("Glossary", id="open", class_name="gloss-button"),

            dbc.Modal(
                [
                    dbc.ModalHeader("Glossary"),
                    dbc.ModalBody(
                        dbc.Table.from_dataframe(da.GetGlossaryTerms(),
                                                 class_name="modal-table",
                                                 striped=True,
                                                 bordered=True, 
                                                 hover=True)
                        ),
                    dbc.ModalFooter(
                        dbc.Button("Close", id="close", className="ml-auto")
                    ),
                ],
                id="modal",
                is_open=False,  # Do not open the modal at opening the webpage.
                backdrop=True,  # Modal can be closed by clicking on backdrop
                scrollable=True,  # Scrollable in case of large amount of text
                centered=True,  # Vertically center modal 
                keyboard=True,  # Close modal when escape is pressed
                fade=False, # Makes modal appear instantly
              ),
          ]),
      ]),

      # The central area where the data visualizations will be
      html.Div(id="main", children=[
          # Where question detail data visualizations go
          html.Div(id="top-infopane-student", className="infopane", children=[
              #css grid won't show a div if it is empty so here is a placeholder
              html.H3(children="Top Info", className="header"),
              html.Div(id="detail-pane-student")
          ]),

          # Where the initial data visualization will go
          html.Div(id="left-infopane-student", className="infopane", children=[
              html.H3(children="Pre-Test", id="initial-title", className="header"),
          ]),

          # Where the revised data visualization will go
          html.Div(id="right-infopane-student", className="infopane", children=[
              html.H3(children="Post-Test", id="revised-title", className="header"),
          ]),
      ]),   

      # Somewhere to point no-output callbacks to ...
      html.Div(id='placeholder', style={"display":"none"})
  ])

  APP.logger.info("3.  Webpage ready to view, " + datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

  return gLayout



## ------------- vvv  Callbacks for the Student Details Pane  vvv ----------------

## This is the main handler for all the student detail callbacks.
def HandleStudentDetailRequest(quizID, studentID):
    """
    This is a general function to handle *all* requests for question detail
    graphs.
    """
    quizDF = da.GetScoresDataframe(quizID)

    #print("handler:  ", quizID, studentID)
    components = []
    # components.append( html.H3(children="Top Info", className="header") )

    try:
      if not studentID == "root":
        components.append( widgetbuilder.gBuilder.GetStudentDetailsGraph(quizID, studentID, quizDF) )
    except Exception as e:
      message = "Error loading quiz detail " + str((quizID, studentID)) + "  ::  " + str(e)                  
      components.append( html.P(children=message, className="graph-component-message") )

    return components
    

def RegisterCallbacks(dashapp):
  # Selecting a question on the DECA panes
  @dashapp.callback( Output('deca-student', 'children'),
                     Input(dataUtils.GetGraphComponentName('deca','student','InitialScore'), 'tapNodeData'), 
                     Input(dataUtils.GetGraphComponentName('deca','student','RevisedScore'), 'tapNodeData') )
  def displayStudentDecaInitialDetail(*args): 
      global gWhichView
      global gQuizOptions
      quizID = appUtils.GetSelectedQuizIDCookie(gQuizOptions[0]['value'])
      whichScores, data = appUtils.StripContextInfo(dash.callback_context, gWhichView)

      if data is not None:
        return HandleStudentDetailRequest(quizID, data)
      else:
        return html.P(children="Select a node on the graph for more details", className="top-pane-message")


  # Selecting a heatmap question detail
  @dashapp.callback( Output('hm-student', 'children'),
                     Input(dataUtils.GetGraphComponentName('heatmap','student','InitialScore'), 'clickData'),
                     Input(dataUtils.GetGraphComponentName('heatmap','student','RevisedScore'), 'clickData') )
  def displayStudentHmInitialDetail(*args): 
      global gWhichView
      global gQuizOptions
      quizID = appUtils.GetSelectedQuizIDCookie(gQuizOptions[0]['value'])
      whichScores, data = appUtils.StripContextInfo(dash.callback_context, gWhichView)

      if data is not None:
        return HandleStudentDetailRequest(quizID, data)
      else:
        return html.P(children="Select a node on the graph for more details", className="top-pane-message")


  # Selecting a multi-dimensional scaling question detail
  @dashapp.callback( Output('mds-student', 'children'),
                     Input(dataUtils.GetGraphComponentName('mds','student','InitialScore'), 'clickData'),
                     Input(dataUtils.GetGraphComponentName('mds','student','RevisedScore'), 'clickData') )
  def displayStudentMdsInitialDetail(*args): 
      global gWhichView
      global gQuizOptions
      quizID = appUtils.GetSelectedQuizIDCookie(gQuizOptions[0]['value'])
      whichScores, data = appUtils.StripContextInfo(dash.callback_context, gWhichView)

      if data is not None:
        return HandleStudentDetailRequest(quizID, data)
      else:
        return html.P(children="Select a node on the graph for more details", className="top-pane-message")


  # Selecting a item descrimination scaling question detail
  @dashapp.callback( Output('ids-student', 'children'),
                     Input(dataUtils.GetGraphComponentName('ids','student','InitialScore'), 'clickData'),
                     Input(dataUtils.GetGraphComponentName('ids','student','RevisedScore'), 'clickData') )
  def displayStudentIdsInitialDetail(*args): 
      global gWhichView
      global gQuizOptions
      quizID = appUtils.GetSelectedQuizIDCookie(gQuizOptions[0]['value'])
      whichScores, data = appUtils.StripContextInfo(dash.callback_context, gWhichView)

      if data is not None:
        return HandleStudentDetailRequest(quizID, data)
      else:
        return html.P(children="Select a node on the graph for more details", className="top-pane-message")


  # Selecting a traditional question detail
  @dashapp.callback( Output('trad-student', 'children'),
                Input(dataUtils.GetGraphComponentName('trad','student','InitialScore'), 'clickData'),
                Input(dataUtils.GetGraphComponentName('trad','student','RevisedScore'), 'clickData') )
  def displayStudentTradInitialDetail(*args):
      global gWhichView
      global gQuizOptions
      quizID = appUtils.GetSelectedQuizIDCookie(gQuizOptions[0]['value'])
      whichScores, data = appUtils.StripContextInfo(dash.callback_context, gWhichView)

      if data is not None:
        return HandleStudentDetailRequest(quizID, data)
      else:
        return html.P(children="Select a node on the graph for more details", className="top-pane-message")


 # This callback is for when the glossary button is clicked; Shows modal/glossary popup
 # @dashapp.callback(
 #     Output("modal", "is_open"),
 #     [Input("open", "n_clicks"), Input("close", "n_clicks")],
 #     [State("modal", "is_open")] )
 # def toggle_modal(n1, n2, is_open):
 #     if n1 or n2:
 #         return not is_open
 #     return is_open
  

  ## ------------- vvv  Callback for the Side Menu vvv ----------------
  @dashapp.callback(Output('left-infopane-student', 'children'),
                    Output('right-infopane-student', 'children'),
                    Output('detail-pane-student', 'children'),
                    Input('side-menu-student', 'value'),
                    Input('quizselect-dropdown-student', 'value') )
  def displayStudentTabMenuData(whichAnalysis, quizItemValue):
      global gQuizOptions
      quizID = appUtils.GetSelectedQuizIDCookie(gQuizOptions[0]['value'])
      quizDF = da.GetScoresDataframe(quizID)  ## RPW:  Move this below?

      APP.logger.info("Displaying " + str(whichAnalysis) + " " + str(quizItemValue)) 

      # If this is being called because of the quiz selection drop down, then change the 
      # quiz ID.  Or if the quizID is not properly stored in the application state singleton
      if (quizID == None) or (dash.callback_context.triggered[0]['prop_id'].strip() == 'quizselect-dropdown-student.value'):
        quizID = quizItemValue  
        appUtils.SetSelectedQuizIDCookie(quizID, dash.callback_context)

      # Check to see if a reload of the dataframe is really needed.
      if True: # widgetbuilder.gBuilder.IsReloadNeeded(quizID, quizDF):
        quizDF = da.GetScoresDataframe(quizID)
        widgetbuilder.gBuilder.PopulateGraphs(quizID, quizDF) 

      # Initialize the Initial panel HTML components
      componentsLeft = []
      componentsLeft.append( html.H3(children="Pre-Test", id="initial-title", className="header") )
      graphObject, contextDict = widgetbuilder.gBuilder.GetGraph(whichAnalysis, "student", "InitialScore")     
      componentsLeft.append( graphObject)
      if (whichAnalysis == "deca"):
        componentsLeft.append(html.P(children="Students further along one axis performed better.", style={'color': 'darkgray'}, className="deca-legend-annotation"))
        componentsLeft.append(html.P(children="Students on different axes cannot be directly compared.", style={'color': 'darkgray'}, className="deca-legend-annotation"))

      # Initialize the Revised panel HTML components
      componentsRight = []
      componentsRight.append( html.H3(children="Post-Test", id="revised-title", className="header") )
      graphObject, contextDict = widgetbuilder.gBuilder.GetGraph(whichAnalysis, "student", "RevisedScore")    
      componentsRight.append( graphObject )
      if (whichAnalysis == "deca"):
        componentsRight.append(html.P(children="Students further along one axis performed better.", style={'color': 'darkgray'}, className="deca-legend-annotation"))
        componentsRight.append(html.P(children="Students on different axes cannot be directly compared.", style={'color': 'darkgray'}, className="deca-legend-annotation"))

      # To solve the detail graph question, each tab will also generate an empty div that will be used as a unique output
      # Initialize the Top Infopane HTML components
      componentsTop = []
      componentsTop.append( html.Div(id=whichAnalysis+"-student", children=[
        html.P(children="Select a node on the graph for more details", className="top-pane-message")
      ]))

      return componentsLeft, componentsRight, componentsTop
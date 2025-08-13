## This is the "Analysis by Question" app 
from os import link
from pydoc import classname
import datetime

import dash
from dash import dcc
import dash_bootstrap_components as dbc
from dash import html
from dash.dependencies import Input, Output, State

from evopie import APP
import evopie.datadashboard.utils as appUtils

import datalayer.dbaccess as da
from datalayer import LOGGER
#import analysislayer.widgetbuilder as widgetbuilder
import analysislayer.widgetupdater as widgetupdater
import analysislayer.utils as dataUtils


gWhichView = "QuestionView"
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
  defaultQuizVal = -1
  if len(gQuizOptions) > 0:
     defaultQuizVal = gQuizOptions[0]['value']
  quizIDstr = appUtils.GetSelectedQuizIDCookie(defaultQuizVal)

  # These are the fake dataframes will use until we integrate with EvoPIE
  LOGGER.info('')
  LOGGER.info('--' + __name__ + '-'.ljust(50, '-'))
  LOGGER.info("1.  Reinitializing, " + datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

  # Create the web page layout
  LOGGER.info("2.  Creating the layout.")

  """
  LWR: I wonder if we should switch to a format for multi-pages like the main evopie page.
  Another option that may or may not work is to add our pages to their routes_pages.py
  I am not sure if this would work, but this could solve href problem when trying to go 
  back to their index page
  """

  gLayout = html.Div(children=[
      
      # The drop-down quiz selector at the top
      html.Div(id="nav-topbar", className="rectangle", children=[
          html.Li(className="nav", children=[
              dcc.Link('Analysis by Question', href='/datadashboard/question/', className="nav-link here"),
              dcc.Link('Analysis by Student', href='/datadashboard/student/', className="nav-link"),
              dcc.Link('Back to EvoPIE', href='/', className="nav-link", refresh=True)
          ]),
          dcc.Dropdown(id="quizselect-dropdown-question", 
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
            dcc.Tabs(id="side-menu-question",
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
          html.Div(id="top-infopane-question", className="infopane", children=[
              #css grid won't show a div if it is empty so here is a placeholder
              html.H3(children="Top Info", id="topinfo-title", className="header"),
                html.Div(id="detail-pane")
          ]),

          # Where the initial data visualization will go
          html.Div(id="left-infopane", className="infopane", children=[
              html.H3(children="Pre-Test", id="initial-title", className="header"),
          ]),

          # Where the revised data visualization will go
          html.Div(id="right-infopane", className="infopane", children=[
              html.H3(children="Post-Test", id="revised-title", className="header"),
          ]),
      ]),   

      #dcc.Interval(id="interval-component", interval=15_000, n_intervals=0),  # Tic updater every 15 seconds, for drop-down updates

      # Somewhere to point no-output callbacks to ...
      html.Div(id='placeholder', style={"display":"none"})
  ])

  LOGGER.info("3.  Webpage ready to view, " + datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

  return gLayout


## ------------- vvv  Callbacks for the Question Details Pane  vvv ----------------

## This is the main handler for all the question detail callbacks.
def HandleQuestionsDetailRequest(quizID, questionID, whichScores):
    """
    This is a general function to handle *all* requests for question detail
    graphs.
    """
    components = []

    try:
        quizDetailDF = da.GetQuestionDetailDataframe(quizID, questionID, whichScores)        
        if not questionID == "root": 
            components.append( widgetupdater.GetQuestionDetailHeader(quizDetailDF, questionID, whichScores) )
            components.append( widgetupdater.GetQuestionDetailsGraph(quizDetailDF, questionID, whichScores) )
        
    except Exception as e:
        message = "Error loading quiz detail " + str((quizID, questionID)) + "  ::  " + str(e)                  
        components.append( html.P(children=message, className="graph-component-message") )

    return components

 

def RegisterCallbacks(dashapp): 
  # Selecting a question on the DECA panes
  @dashapp.callback( Output('deca', 'children'),
                     Input(dataUtils.GetGraphComponentName('deca','question','InitialScore'), 'tapNodeData'), #each one of these will need its own callback since it throws an error when all the inputs are not used
                     Input(dataUtils.GetGraphComponentName('deca','question','RevisedScore'), 'tapNodeData'), prevent_initial_call=True )#they can be separated by visualization type, generate a new top pane fro each graph too so that way they can have multiple outputs
  def displayDecaInitialDetail(*args):
      global gWhichView
      global gQuizOptions
      quizID = appUtils.GetSelectedQuizIDCookie(gQuizOptions[0]['value'])
      whichScores, data = appUtils.StripContextInfo(dash.callback_context, gWhichView)

      if data is not None:
        return HandleQuestionsDetailRequest(quizID, data, whichScores)
      else:
        return html.P(children="Select a node on the graph for more details", className="top-pane-message")


  # Selecting a question on the heat map panes
  @dashapp.callback( Output('hm', 'children'),
                  #they can be separated by visualization type, generate a new top pane fro each graph too so that way they can have multiple outputs
                     Input(dataUtils.GetGraphComponentName('heatmap','question','InitialScore'), 'clickData'),
                     Input(dataUtils.GetGraphComponentName('heatmap','question','RevisedScore'), 'clickData') )
  def displayHmInitialDetail(*args): 
      global gWhichView
      global gQuizOptions
      quizID = appUtils.GetSelectedQuizIDCookie(gQuizOptions[0]['value'])
      whichScores, data = appUtils.StripContextInfo(dash.callback_context, gWhichView)

      if data is not None:
        return HandleQuestionsDetailRequest(quizID, data, whichScores)
      else:
        return html.P(children="Select a node on the graph for more details", className="top-pane-message")


  # Selecting a question on the mds panes
  @dashapp.callback( Output('mds', 'children'),
                     Input(dataUtils.GetGraphComponentName('mds','question','InitialScore'), 'clickData'),
                     Input(dataUtils.GetGraphComponentName('mds','question','RevisedScore'), 'clickData') )
  def displayMdsInitialDetail(*args): 
      global gWhichView
      global gQuizOptions
      quizID = appUtils.GetSelectedQuizIDCookie(gQuizOptions[0]['value'])
      whichScores, data = appUtils.StripContextInfo(dash.callback_context, gWhichView)

      if data is not None:
        return HandleQuestionsDetailRequest(quizID, data, whichScores)
      else:
        return html.P(children="Select a node on the graph for more details", className="top-pane-message")


  # Selecting a question on the item discrimination panes
  @dashapp.callback( Output('ids', 'children'),
                     Input(dataUtils.GetGraphComponentName('ids','question','InitialScore'), 'clickData'),
                     Input(dataUtils.GetGraphComponentName('ids','question','RevisedScore'), 'clickData') )
  def displayIdsInitialDetail(*args):
      global gWhichView
      global gQuizOptions
      quizID = appUtils.GetSelectedQuizIDCookie(gQuizOptions[0]['value'])
      whichScores, data = appUtils.StripContextInfo(dash.callback_context, gWhichView)

      if data is not None:
        return HandleQuestionsDetailRequest(quizID, data, whichScores)
      else:
        return html.P(children="Select a node on the graph for more details", className="top-pane-message")


  # Selecting a question on the traditional panes
  @dashapp.callback( Output('trad', 'children'),
                     Input(dataUtils.GetGraphComponentName('trad','question','InitialScore'), 'clickData'),
                     Input(dataUtils.GetGraphComponentName('trad','question','RevisedScore'), 'clickData') )
  def displayTradInitialDetail(*args): 
      global gWhichView
      global gQuizOptions
      quizID = appUtils.GetSelectedQuizIDCookie(gQuizOptions[0]['value'])
      whichScores, data = appUtils.StripContextInfo(dash.callback_context, gWhichView)

      if data is not None:
        return HandleQuestionsDetailRequest(quizID, data, whichScores)
      else:
        return html.P(children="Select a node on the graph for more details", className="top-pane-message")



 # This callback is for when the glossary button is clicked; Shows modal/glossary popup
  @dashapp.callback(
      Output("modal", "is_open"),
      [Input("open", "n_clicks"), Input("close", "n_clicks")],
      [State("modal", "is_open")] )
  def toggle_modal(n1, n2, is_open):
      if n1 or n2:
          return not is_open
      return is_open
  

  ## ------------- vvv  Callback for the Side Menu vvv ----------------
  @dashapp.callback(Output('left-infopane', 'children'),
                    Output('right-infopane', 'children'),
                    Output('detail-pane', 'children'),
                    Input('side-menu-question', 'value'),
                    Input('quizselect-dropdown-question', 'value') )
  def displayTapMenuData(whichAnalysis, quizItemValue):
      global gQuizOptions
      gQuizOptions = da.GetQuizOptionList()   # RPW:  Added to repop quiz items on side menu seln, 8/6/25
      quizID = appUtils.GetSelectedQuizIDCookie(gQuizOptions[0]['value'])
      #quizDF = da.GetScoresDataframe(quizID)

      # Now we have appUtils.gApplicationState.QuizDropDown, so we can set the default/selected item
      LOGGER.info("Displaying " + str(whichAnalysis) + " " + str(quizItemValue)) 

      # If this is being called because of the quiz selection drop down, then change the 
      # quiz ID.  Or if the quizID is not properly stored in the application state singleton
      if (quizID == None) or (dash.callback_context.triggered[0]['prop_id'].strip() == 'quizselect-dropdown-question.value'):
        quizID = quizItemValue  
        appUtils.SetSelectedQuizIDCookie(quizID, dash.callback_context)

      # Check to see if a reload of the dataframe is really needed.
      #if widgetbuilder.gBuilder.IsReloadNeeded(quizID, quizDF):
      #  quizDF = da.GetScoresDataframe(quizID)  
      #  widgetbuilder.gBuilder.PopulateGraphs(quizID, quizDF) 

      # Initialize the Initial panel HTML components
      componentsLeft = []
      componentsLeft.append( html.H3(children="Pre-Test", id="initial-title", className="header") )
      #graphObject, contextDict = widgetbuilder.gBuilder.GetGraph(whichAnalysis, "question", "InitialScore")
      graphObject, contextDict = widgetupdater.GetGraph(quizID, whichAnalysis, "question", "InitialScore")
      componentsLeft.append( graphObject )
      if (whichAnalysis == "deca"):
        componentsLeft.append(html.P(children="Questions further along one axis are strictly harder in terms of student performance.", style={'color': 'darkgray'}, className="deca-legend-annotation"))
        componentsLeft.append(html.P(children="Questions on different axes cannot be directly compared.", style={'color': 'darkgray'}, className="deca-legend-annotation"))
        componentsLeft.append(html.P(children="Green represents informatively easy questions", style={'color': 'green'}, className="deca-legend-annotation"))
        componentsLeft.append(html.P(children="Red represents informatively hard questions", style={'color': 'red'}, className="deca-legend-annotation"))

      # Initialize the Revised panel HTML components
      componentsRight = []
      componentsRight.append( html.H3(children="Post-Test", id="revised-title", className="header") )
      #graphObject, contextDict = widgetbuilder.gBuilder.GetGraph(whichAnalysis, "question", "RevisedScore")     
      graphObject, contextDict = widgetupdater.GetGraph(quizID, whichAnalysis, "question", "RevisedScore")
      componentsRight.append( graphObject )
      if (whichAnalysis == "deca"):
        componentsRight.append(html.P(children="Questions further along one axis are strictly harder in terms of student performance.", style={'color': 'darkgray'}, className="deca-legend-annotation"))
        componentsRight.append(html.P(children="Questions on different axes cannot be directly compared.", style={'color': 'darkgray'}, className="deca-legend-annotation"))
        componentsRight.append(html.P(children="Green represents informatively easy questions", style={'color': 'green'}, className="deca-legend-annotation"))
        componentsRight.append(html.P(children="Red represents informatively hard questions", style={'color': 'red'}, className="deca-legend-annotation"))

      # To solve the detail graph question, each tab will also generate an empty div that will be used as a unique output
      # Initialize the Top Infopane HTML components
      componentsTop = []
      componentsTop.append( html.Div(id=whichAnalysis, children=[
        html.P(children="Select a node on the graph for more details", className="top-pane-message")
      ]))

      return componentsLeft, componentsRight, componentsTop
  

  ## ------------- vvv  Callback for Top-Bar Click  vvv ----------------
  @dashapp.callback(Output('quizselect-dropdown-question', 'options'),
                    Input( 'nav-topbar', 'n_clicks') )
  def updateDropDown(n_inteval):
      global gQuizOptions
      gQuizOptions = da.GetQuizOptionList(False)   # RPW:  Added to repop quiz items on side menu seln, 8/6/25
      print("DBG:::  updating the options of the drop down (Q) ...", gQuizOptions)
      return [{'label':gQuizOptions, 'value':gQuizOptions}]


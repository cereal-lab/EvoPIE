# pylint: disable=no-member
# pylint: disable=E1101

# This module is meant to provide tools to produce plots in plotly for the
# data analytics dashboard.

import os, sys
import numpy as np

import evopie.datadashboard.formatting as formatting

# For My plotly testing:
try:
  import plotly.express as px
  import plotly.io as pio
  import plotly.graph_objects as go
except:
  pass


def GetPrefabricatedExampleBoxPlot():
   # Render out an HTML file with the a test interactive boxplot
   boxplotHTML = ""
   try:
     df = px.data.tips()  # Pre-loaded data that comes in plotly.express
     fig = px.box(df, x="time", y="total_bill", points="all")
     boxplotHTML = pio.to_html(fig,
                               default_width='500px', default_height='500px', \
                               full_html=False)
   except:
     boxplotHTML = "  <p>A boxplot should be here, but there was a problem with plotly.</p>"

   return boxplotHTML


def GetSimpleHeatMap(dataframe, quizID, valueColName='InitialScore'):
  plotDataObj = {'x':list(map(str,dataframe.QuestionID.values.tolist())), \
                 'y':list(map(str,dataframe.StudentID.values.tolist())), \
                 'z':dataframe[valueColName].values.tolist() }

  # Make a simple heatmap out of a data matrix of 0's and 1's.
  heatmapHTML = ""

  try:
    titleText = "Quiz " + str(quizID) + " " + valueColName
    ticktext = ['Incorrect', 'Correct']
    tickvals = [0.0, 1.0]
    dcolorsc = [[ 0.0, '#dddddd'], [1.0, '#0062C2']]

    # Create the graph object
    hm = go.Heatmap(plotDataObj, \
                    colorscale=dcolorsc, \
                    colorbar=dict(thickness=25, tickvals=tickvals, ticktext=ticktext))
    fig = go.Figure(data=[hm], layout=go.Layout(title=go.layout.Title(text=titleText)))
    fig = fig.update_xaxes(title_text="Questions")
    fig = fig.update_yaxes(title_text="Students")

    heatmapHTML = fig.to_html(fig,\
                              default_width='500px', default_height='500px', \
                              full_html=False)
  except Exception as error:
    heatmapHTML = "  <p><b>ERROR:</b> A heatmap should be here, but there was a problem with plotly.</p>"
    heatmapHTML += " <p><i>" + str(error) + "</i></p"

  return heatmapHTML

# pylint: disable=no-member
# pylint: disable=E1101

# This module is meant to provide tools to produce plots in plotly for the
# data analytics dashboard.

import os, sys
import numpy as np


# For My plotly testing:
try:
  import plotly.express as px
  import plotly.io as pio
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

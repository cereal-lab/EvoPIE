# pylint: disable=no-member
# pylint: disable=E1101

# This module is provides a way to check if the user should be able to access the dashboard at all.
# RPW: I'd rather this be in dbaccess.py, but there's a circular reference with respect to the dashboard_context.
#      Once that is resolved, move this back.

import datalayer.models as models  # RPW:  Move this to datalayer
from flask_login import current_user



def IsValidDashboardUser():
  """
  Determine whether the user is properly logged in and is one of the roles that
  is permitted to see the dashboard data:  admin or instructor.  Return -1 for 
  not authenticated at all, 0 if authenticated but not a valid role, 1 if the role 
  instructor or admin.
  """
  validated = -1
  user = None

  # Try to get the current authenticated user and checking it's role
  try:
    if (current_user.is_authenticated):
      validated = 0
      user = models.User.query.filter(models.User.id == current_user.id).first()

      # If we didn't find a current user, refuse to validate the user
      if (user == None):    
        validated = -1

      # Otherwise, make sure the user is an instructor or an admin
      elif (user.is_instructor() or user.is_admin()):
        validated = 1

  # If we had any kind of problem, refuse to validate the user
  except:
    validated = -1

  return validated

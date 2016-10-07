"""
Very simple Flask web site, with one page
displaying a course schedule.

"""

import flask
from flask import render_template
from flask import request
from flask import url_for

import json
import logging

# Date handling 
import arrow # Replacement for datetime, based on moment.js
import datetime # But we still need time
from dateutil import tz  # For interpreting local times

# Our own module
import pre  # Preprocess schedule file


###
# Globals
###
app = flask.Flask(__name__)
import CONFIG
currentDate = arrow.now()

###
# Pages
###

@app.route("/")
@app.route("/index")
@app.route("/schedule")
def index():
  app.logger.debug("Main page entry")
  if 'schedule' not in flask.session:
      app.logger.debug("Processing raw schedule file")
      raw = open(CONFIG.schedule)
      flask.session['schedule'] = pre.process(raw)
      print(format_arrow_date(currentDate))
  
  flask.g.today = arrow.now()
  return flask.render_template('syllabus.html')


@app.errorhandler(404)
def page_not_found(error):
    app.logger.debug("Page not found")
    flask.session['linkback'] =  flask.url_for("index")
    return flask.render_template('page_not_found.html'), 404

#################
#
# Functions used within the templates
#
#################

@app.template_filter( 'fmtdate' )
def format_arrow_date( date ):
    try: 
        normal = arrow.get( date )
        return normal.format("ddd MM/DD/YYYY")
    except:
        return "(bad date)"


@app.template_filter( 'isweek' )
def format_week( i  ):
    """
    args :  a string of date (i)
	
    returns : a bool value   
              True if current date is within 7 days past date (i) 
	"""
    refdate = i.split()
    date = format_arrow_date(currentDate).split()
    isSeven = False
    fmt = '%m/%d/%Y'
    dtweek = datetime.datetime.strptime(date[1],fmt)
    refweek = datetime.datetime.strptime(refdate[1],fmt)
    dtweek = dtweek.timetuple()
    refweek = refweek.timetuple()
    
    if (dtweek.tm_yday - refweek.tm_yday <= 7) and (dtweek.tm_yday - refweek.tm_yday >=0):
        isSeven = True
 
    return isSeven
    

#############
#    
# Set up to run from cgi-bin script, from
# gunicorn, or stand-alone.
#


if __name__ == "__main__":
    # Standalone, with a dynamically generated
    # secret key, accessible outside only if debugging is not on
    import uuid
    app.secret_key = str(uuid.uuid4())
    app.debug=CONFIG.DEBUG
    app.logger.setLevel(logging.DEBUG)
    print("Opening for global access on port {}".format(CONFIG.PORT))
    app.run(port=CONFIG.PORT, host="0.0.0.0")
else:
    # Running from cgi-bin or from gunicorn WSGI server, 
    # which makes the call to app.run.  Gunicorn may invoke more than
    # one instance for concurrent service. It is essential all
    # instances share the same secret key for session management. 
    app.secret_key = CONFIG.secret_key
    app.debug=False


# -*- coding: utf-8 -*-
# MAINTAINER @totetmatt <matthieu.totet@gmail.com>
# Simple broadcast system for Gephi Streaming plugin

import flask
import json
import Queue
from flask.signals  import Namespace
import cherrypy
from paste.translogger import TransLogger

# Custom libs for managing Exception or just Help classes.
from graphStreamException import *
from graphStreamHelper import *

# Flask bootstrap 
app = flask.Flask(__name__)

# We create a signals channel that will brodcast an incoming action into all subscribers
# Bascially all opened HTTP connections will be subscribing this to receive event
customSignals = Namespace()
eventChannel = customSignals.signal('eventChannel')

# True if the jsonString given is a well formed json and if it's a valid action (see graphStreamHelper.validActions)
# Needed because any error on the action format makes the client disconect
## TO DO : Put that in graphStreamHelper
def actionValidator(jsonString):
    try:
        #It's possible to have multiple actions
        data = json.loads(jsonString)
        for action in data:
            if action not in GraphStreamHelper.validActions:
                return False
        return True
    except:
        return False

# Not clear, but the client is perfoming somehow a 'callback' to the same entrypoint but as POST. So just handeling it wihout any process
@app.route( '/stream',methods=['POST'] )
def streamPost():
    return flask.Response(status=200)    

# The entrypoint for Gephi as Client
@app.route( '/stream',methods=['GET'] )
def stream(): 
    #
    queue = Queue.Queue() 
    # Create a Generator, it's the way to be to do HTTP Stream in Flask
    def streamProcess():

        # Subscribe to the channel, it will just put received data into the queue. 
        # Can be highly optimized for sure ;)
        @eventChannel.connect
        def eventChannelSubscriber(data):
            queue.put(data)

        #Looping until death, if Queue is empty do nothing otherwise send the data
        while True:
            try:  
                e = queue.get()
                if e is None: break
                # '\r\n are requiered'
                yield e + '\r\n'
            except:
                print "Connection closed"
                return
    return flask.Response( streamProcess(), mimetype= 'application/json',content_type="application/json" )   

# Basic entrypoint for broadcasting data
@app.route( '/action' , methods=['POST'] )
def default():
    print "data"
    print flask.request.data
    if not actionValidator(flask.request.data):
        raise WebServiceException("Action provided incorrect") 
    try:
        eventChannel.send(flask.request.data)
        return flask.Response(status=200)
    except Exception as e:
        raise WebServiceException(e,status_code=400) 

# An RestFul service like to perfom actions.
@app.route( '/<action>', methods=['POST'] )
def action(action):
    if action not in GraphStreamHelper.validActions:
        raise WebServiceException("Action provided incorrect") 
    try:
        data= json.loads(flask.request.data)
        eventChannel.send(json.dumps({action:data}))
        return flask.Response(status=200)
    except Exception as e:
        raise WebServiceException(e,status_code=400) 

# Handling Exception
@app.errorhandler(WebServiceException)
def handleInvalidUsage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response
    
if __name__ == "__main__":
    ##app.run(threaded=True,host='0.0.0.0')
    # Enable WSGI access logging via Paste
    app_logged = TransLogger(app)

    # Mount the WSGI callable object (app) on the root directory
    cherrypy.tree.graft(app_logged, '/')

    # Set the configuration of the web server
    cherrypy.config.update({
        #'engine.autoreload.on': True,
        'log.screen': True,
        'server.socket_port': 5000,
        'server.socket_host': '0.0.0.0'
    })

    # Start the CherryPy WSGI web server
    cherrypy.engine.start()
    cherrypy.engine.block()

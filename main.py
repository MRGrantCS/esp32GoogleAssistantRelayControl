try:
  import usocket as socket
except:
  import socket

from adaioCon import aioCon

try:
  import uos as os
except:
  import os

import network

try:
  import utime as time
except:
  import time

from umqtt.robust import MQTTClient

import esp
esp.osdebug(None)

import gc
gc.collect()

from settingsGetSet import setSettings, getSettings

from microWebSrv import MicroWebSrv

#initialise variables
AP = False
filename = 'settings.json'
ssid = ''
password = ''


#--- Set up wifi connection
try:
  #--- Try to connect as Station
  ssid , password = getSettings(filename, AP)
  station = network.WLAN(network.STA_IF)
  station.active(True)
  station.connect(ssid, password)
  #--- timed retries to allow esp32 to connect to network
  tries = 0  
  while tries < 5 and station.isconnected() == False:
    tries += 1
    print("Connection unsuccessful. Attempt:", tries)
    time.sleep(3)
  #--- raise exception if unable to connect to an AP
  if station.isconnected() == False:
    print('Could not connect as Station')  
    raise Exception
  print('Station Connection successful')
  #--- Print IP details
  print(station.ifconfig())

except Exception:
  #--- switch to AP mode, using AP details in settings.json
  AP = True
  ssid , password = getSettings(filename, AP)
  ap = network.WLAN(network.AP_IF)
  ap.active(True)
  while ap.active() == False:
    pass
  ap.config(essid=ssid, password=password)
  print('Access Point Created')
  #--- Print IP details
  print(ap.ifconfig())

finally:
  print("Network details:")
  print("SSID =",ssid)
  print("Password =",password)

#--- aiocon


# ----------------------------------------------------------------------------
@MicroWebSrv.route('/aio')
def _httpHandlerAIOGet(httpClient, httpResponse) :
	content = """\
	<!DOCTYPE html>
	<html lang=en>
        <head>
        	<meta charset="UTF-8" />
            <title>AIO GET</title>
        </head>
        <body>
            <h1>AIO GET</h1>
            Client IP address = %s
            <br />
            <input type="button" id='script' name="scriptbutton" value=" Run Script ">
			</form>
        </body>
    </html>
	""" % (httpClient.GetIPAddr())
	httpResponse.WriteResponseOk( headers		 = None,
								  contentType	 = "text/html",
								  contentCharset = "UTF-8",
								  content 		 = content )
	aioCon()



@MicroWebSrv.route('/test')
def _httpHandlerTestGet(httpClient, httpResponse) :
	content = """\
	<!DOCTYPE html>
	<html lang=en>
        <head>
        	<meta charset="UTF-8" />
            <title>TEST GET</title>
        </head>
        <body>
            <h1>TEST GET</h1>
            Client IP address = %s
            <br />
			<form action="/test" method="post" accept-charset="ISO-8859-1">
				SSID: <input type="text" name="SSID"><br />
				Password : <input type="text" name="PSK"><br />
				<input type="submit" value="Submit">
			</form>
        </body>
    </html>
	""" % httpClient.GetIPAddr()
	httpResponse.WriteResponseOk( headers		 = None,
								  contentType	 = "text/html",
								  contentCharset = "UTF-8",
								  content 		 = content )


@MicroWebSrv.route('/test', 'POST')
def _httpHandlerTestPost(httpClient, httpResponse) :
	formData  = httpClient.ReadRequestPostedFormData()
	SSID = formData["SSID"]
	PSK  = formData["PSK"]
	content   = """\
	<!DOCTYPE html>
	<html lang=en>
		<head>
			<meta charset="UTF-8" />
            <title>TEST POST</title>
        </head>
        <body>
            <h1>TEST POST</h1>
            SSID = %s<br />
            PSK = %s<br />
            Restart after update <br />
        </body>
    </html>
	""" % ( MicroWebSrv.HTMLEscape(SSID),
		    MicroWebSrv.HTMLEscape(PSK) )
	httpResponse.WriteResponseOk( headers		 = None,
								  contentType	 = "text/html",
								  contentCharset = "UTF-8",
								  content 		 = content )
	setSettings("settings.json", SSID, PSK)


@MicroWebSrv.route('/edit/<index>')             # <IP>/edit/123           ->   args['index']=123
@MicroWebSrv.route('/edit/<index>/abc/<foo>')   # <IP>/edit/123/abc/bar   ->   args['index']=123  args['foo']='bar'
@MicroWebSrv.route('/edit')                     # <IP>/edit               ->   args={}
def _httpHandlerEditWithArgs(httpClient, httpResponse, args={}) :
	content = """\
	<!DOCTYPE html>
	<html lang=en>
        <head>
        	<meta charset="UTF-8" />
            <title>TEST EDIT</title>
        </head>
        <body>
	"""
	content += "<h1>EDIT item with {} variable arguments</h1>"\
		.format(len(args))
	
	if 'index' in args :
		content += "<p>index = {}</p>".format(args['index'])
	
	if 'foo' in args :
		content += "<p>foo = {}</p>".format(args['foo'])
	
	content += """
        </body>
    </html>
	"""
	httpResponse.WriteResponseOk( headers		 = None,
								  contentType	 = "text/html",
								  contentCharset = "UTF-8",
								  content 		 = content )

# ----------------------------------------------------------------------------

def _acceptWebSocketCallback(webSocket, httpClient) :
	print("WS ACCEPT")
	webSocket.RecvTextCallback   = _recvTextCallback
	webSocket.RecvBinaryCallback = _recvBinaryCallback
	webSocket.ClosedCallback 	 = _closedCallback

def _recvTextCallback(webSocket, msg) :
	print("WS RECV TEXT : %s" % msg)
	webSocket.SendText("Reply for %s" % msg)

def _recvBinaryCallback(webSocket, data) :
	print("WS RECV DATA : %s" % data)

def _closedCallback(webSocket) :
	print("WS CLOSED")

# ----------------------------------------------------------------------------

#routeHandlers = [
#	( "/test",	"GET",	_httpHandlerTestGet ),
#	( "/test",	"POST",	_httpHandlerTestPost )
#]

srv = MicroWebSrv(webPath='www/')
srv.MaxWebSocketRecvLen     = 256
srv.WebSocketThreaded		= False
srv.AcceptWebSocketCallback = _acceptWebSocketCallback
srv.Start()

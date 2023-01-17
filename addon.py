__author__ = "Phil Busby"
__credits__ = ["dreamcat4 for LG TV Remote 2011","msloth for LG TV Remote 2015", "ubaransel for LG TV Remote 2012-2014","BillyNate","filimonic"]
__license__ = "GPL"
__version__ = "1.1.5"
__maintainer__ = "Phil Busby"
__email__ = "phil.busby@gmail.com"
__status__ = "Developement"
__url__ = "https://github.com/philbusby/Kodi.Screensaver.TurnOffLGTV"

import sys
import xbmcgui
import xbmcaddon
import xbmc
import time
import json
import urllib2
import threading
import os

Addon = xbmcaddon.Addon()
Player = xbmc.Player()

#This is done because we can not import ws4py from resources/lib directly
__path__ = Addon.getAddonInfo('path')
sys.path.insert(1,os.path.join( __path__ ,'resources/lib'))

#This import available only after adding sys.path
from ws4py.client.threadedclient import WebSocketClient

Dialog = xbmcgui.Dialog()
__scriptname__ = Addon.getAddonInfo('name')


class xbmc_log:
    @staticmethod
    def log(message, debuglevel=xbmc.LOGDEBUG):
        xbmc.log("LG TV PowerOff Screensaver :: " + str(message), debuglevel)

class LGTVNetworkShutdownScreensaver():
    TV_TYPE_2015 = '0'
    TV_TYPE_2012 = '1'
    TV_TYPE_2011 = '2'

    ip_address = '0.0.0.0'
    tv_type = '0'
    timeout = 10
    timeout_timer = None
    cli = None
    xbmc_log.log("--------------screensaver start---------------- " ,xbmc.LOGNOTICE)
    def __init__(self):
        _tv_type = Addon.getSetting('tv_type')
        if _tv_type != '':
            self.tv_type = _tv_type
        ip_address = Addon.getSetting('ip_address')
        if ip_address != '':
            xbmc_log.log("1 Tv ip_address is: " + ip_address,xbmc.LOGNOTICE)
            self.ip_address = ip_address

        self.timeout_timer = threading.Timer(self.timeout,self.timeout_timer_fired)
        xbmc_log.log("2 Tv type is: " + self.tv_type,xbmc.LOGNOTICE)
        if self.tv_type == self.TV_TYPE_2015:
            xbmc_log.log("3 Running timer",xbmc.LOGNOTICE)
            self.timeout_timer.start()
            xbmc_log.log("4 Creating shutdowner",xbmc.LOGNOTICE)
            try:
                self.cli = LGTVNetworkShutdown2015(ip_address)
            except RuntimeWarning as detail:
                xbmc_log.log('{W}: (timer error)' + detail.message,xbmc.LOGNOTICE)
        elif self.tv_type == self.TV_TYPE_2012:
            xbmc_log.log("Running timer",xbmc.LOGNOTICE)
            self.timeout_timer.start()
            xbmc_log.log("Creating shutdowneer",xbmc.LOGNOTICE)
            try:
                self.cli = LGTVNetworkShutdown2012(ip_address)
            except RuntimeWarning as detail:
                xbmc_log.log('{W}:' + detail.message)
        elif self.tv_type == self.TV_TYPE_2011:
            Dialog.notification("LG TV 2011","2011 LG TV is not supported yet")
            xbmc_log.log("2011 LG TV is not supported yet",xbmc.LOGNOTICE)
        else:
            xbmc_log.log("Ignoring TV type" + str(self.tv_type))
            xbmc_log.log("finished",xbmc.LOGNOTICE)
            xbmc_log.log("--------------screensaver fail exit---------------- " ,xbmc.LOGNOTICE)

        self.exit()


    def timeout_timer_fired(self):
        xbmc_log.log("Timer fired!",xbmc.LOGNOTICE)
        self.timeout_timer.cancel()
        try:
            self.cli.close()
        except:
            pass

    def exit(self):
        xbmc_log.log("Exiting LGTVNetworkShutdownScreensaver",xbmc.LOGNOTICE)
        try:
            self.timeout_timer.cancel()
        except:
            pass
        try:
            self.cli.close()
        except:
            pass
        try:
            del self.cli
        except:
            pass


class Screensaver(xbmcgui.WindowXMLDialog):
    shutter = None
    class ExitMonitor(xbmc.Monitor):

        def __init__(self, exit_callback):
            self.exit_callback = exit_callback

        def onScreensaverDeactivated(self):
            xbmc_log.log('ExitMonitor: sending exit_callback',xbmc.LOGNOTICE)
            self.exit_callback()

    def onInit(self):
        xbmc_log.log('Screensaver: onInit',xbmc.LOGNOTICE)
        self.monitor = self.ExitMonitor(self.exit)
        self.shutter = LGTVNetworkShutdownScreensaver()

    def exit(self):
        xbmc_log.log('Screensaver: Exit requested',xbmc.LOGNOTICE)
        try:
            self.shutter.exit()
        except:
            pass
        try:
            del self.monitor
        except:
            pass
        self.close()


class LGTVNetworkShutdown2012:
    PAIRING_KEY_PARAMETER_NAME = 'pairing_key_2012'
    HTTP_HEADERS = {"Content-Type": "application/atom+xml"}
    COMMAND_KEY_POWER = str(1) #Refer to http://developer.lgappstv.com/TV_HELP/index.jsp?topic=%2Flge.tvsdk.references.book%2Fhtml%2FUDAP%2FUDAP%2FAnnex+A+Table+of+virtual+key+codes+on+remote+Controller.htm
    COMMAND_KEY_ESM  = str(409)
    COMMAND_KEY_DOWN = str(13)
    COMMAND_KEY_OK   = str(20)
    HTTP_TIMEOUT = 3

    @property
    def client_key(self):
        key = "000000"
        try:
            key_tmp = xbmcaddon.Addon().getSetting(self.PAIRING_KEY_PARAMETER_NAME)
            xbmc_log.log("Pairing key read: " + key_tmp,xbmc.LOGNOTICE)
            #was, xbmc.LOGDEBUG)
            if key_tmp != '':
                key = key_tmp
        except:
            xbmc_log.log("Unable to read pairing key",xbmc.LOGNOTICE)
            #was, xbmc.LOGERROR)
        return key

    def check_connection(self, ip_address):
        try:
            connection_url = 'https://' + ip_address + ':8080'
            xbmc_log.log("Checking https 8080 connection to " + connection_url ,xbmc.LOGNOTICE)
            response=urllib2.urlopen(connection_url,timeout=10)
            xbmc_log.log("Got response, code = " + str(response.getcode()),xbmc.LOGNOTICE)
            if (response.getcode() == 404):
                xbmc_log.log("Check passed, 404 expected {1}",xbmc.LOGNOTICE)
                return True
            else:
                xbmc_log.log("Check failed, response not as expected",xbmc.LOGNOTICE)
                Dialog.notification("LG TV 2012-2014","Seems this is is not TV")
                return False
        except urllib2.HTTPError as err:
            if err.code == 404:
                xbmc_log.log("Check passed, 404 expected {2}",xbmc.LOGNOTICE)
                return True
            else:
                xbmc_log.log("Check failed, response is not as expected" + str(err.code),xbmc.LOGNOTICE)
                Dialog.notification("LG TV 2012-2014","Seems this is is not TV")
                return False
        except urllib2.URLError as err:
            Dialog.notification("LG TV 2012-2014","Connection failed. Maybe IP or type is incorrect?")
            xbmc_log.log("Check failed, URLError",xbmc.LOGNOTICE)
        return False

    def check_registration(self,ip_address):
        data = "<?xml version=\"1.0\" encoding=\"utf-8\"?><auth><type>AuthReq</type><value>" + self.client_key + "</value></auth>"
        try:
            request = urllib2.Request('https://'+ip_address+':8080/roap/api/auth',data=data,headers=self.HTTP_HEADERS)
            response = urllib2.urlopen(request, timeout=self.HTTP_TIMEOUT)
            xbmc_log.log("check_registration https  " + request ,xbmc.LOGNOTICE)
            xbmc_log.log("check_registration response, code = " + str(response.getcode()),xbmc.LOGNOTICE)
            print(response.read())
            return True
        except urllib2.HTTPError as err:
            if err.code == 401:
                xbmc_log.log("Wrong key supplied: " + self.client_key,xbmc.LOGNOTICE)
                Dialog.notification("LG TV 2012-2014","Go to settings to set up key")
                return False
            else:
                xbmc_log.log("Unexpected response code " + str(err.code),xbmc.LOGNOTICE)
        except urllib2.URLError:
            xbmc_log.log("Error checking registration: unable to connect or make a request {URLError)",xbmc.LOGNOTICE)
            return False

    def send_turn_off_command(self,ip_address):
        bIsMusicModeEnabled = ( Addon.getSetting("music_mode_2012") == "true" )
        bIsInMusicMode = ( Player.isPlayingAudio() == 1 )
        xbmc_log.log("music_mode_2012:" + str(Addon.getSetting("music_mode_2012")) + "; bIsMusicModeEnabled:" + str(bIsMusicModeEnabled) + "; bIsInMusicMode:" + str(bIsInMusicMode) + "; Player.isPlayingAudio():" + str(Player.isPlayingAudio()) + "; (bIsMusicModeEnabled and bIsInMusicMode): " + str((bIsMusicModeEnabled and bIsInMusicMode)),xbmc.LOGNOTICE)
        if (not (bIsMusicModeEnabled and bIsInMusicMode) ):
            xbmc_log.log("Sending TURN OFF command",xbmc.LOGNOTICE)
            return self.send_command(ip_address,self.COMMAND_KEY_POWER)
        else:
            i = int(float(Addon.getSetting("music_mode_2012_value")))
            xbmc_log.log("Sending ESM MENU command",xbmc.LOGNOTICE)
            self.send_command(ip_address,self.COMMAND_KEY_ESM)
            while i > 0 :
                xbmc_log.log("Sending DOWN command. i=" + str(i),xbmc.LOGNOTICE)
                self.send_command(ip_address,self.COMMAND_KEY_DOWN)
                i = i - 1
            xbmc_log.log("Sending OK command",xbmc.LOGNOTICE)
            return self.send_command(ip_address,self.COMMAND_KEY_OK);

    def send_command(self,ip_address,command):
        data = "<?xml version=\"1.0\" encoding=\"utf-8\"?><command><name>HandleKeyInput</name><value>" + command + "</value></command>"
        try:
            request = urllib2.Request('https://'+ip_address+':8080/roap/api/command',data=data,headers=self.HTTP_HEADERS)
            response = urllib2.urlopen(request, timeout=self.HTTP_TIMEOUT)
            Dialog.notification("LG TV 2012-2014","Command sent")
            xbmc_log.log("https Command sent",xbmc.LOGNOTICE)
            time.sleep(1);
            return True
        except urllib2.HTTPError as err:
            xbmc_log.log("Error sending PWR_OFF: unable to connect or make a request {HTTPErrror): " + str(err.code),xbmc.LOGNOTICE)
            return False
        except urllib2.URLError:
            xbmc_log.log("Error sending PWR_OFF: unable to connect or make a request {URLError)",xbmc.LOGNOTICE)
            return False

    def __init__(self, ip_address):
        if self.check_connection(ip_address) == True:
            if self.check_registration(ip_address) == True:
                if self.send_turn_off_command(ip_address) == True:
                    xbmc_log.log("Successfully sent PWR_OFF",xbmc.LOGNOTICE)
                else:
                    raise RuntimeWarning('Unable to send PWR_OFF')
            else:
                raise RuntimeWarning('Unable to check registration - possibly wrong key')
        else:
            raise RuntimeWarning('Unable to check connection')

    def close(self):
        pass

class LGTVNetworkShutdown2015(WebSocketClient):
    _msg_id = 0
    _registered = 0
    _power_off_sent = 0
    PAIRING_KEY_PARAMETER_NAME = 'pairing_key_2015'

    def send(self, payload, binary=False):
        self._msg_id = self._msg_id+1
        xbmc_log.log("Sending data to TV:" + payload,xbmc.LOGNOTICE)
        #was , xbmc.LOGDEBUG)
        super(LGTVNetworkShutdown2015,self).send(payload,binary)
    def save_pairing_key(self, key):
        try:
           xbmcaddon.Addon().setSetting(self.PAIRING_KEY_PARAMETER_NAME,key)
           xbmc_log.log("Pairing key saved: " + key,xbmc.LOGNOTICE)
           #was , xbmc.LOGDEBUG)
        except:
            xbmc_log.log("Unable to save pairng key",xbmc.LOGNOTICE)
            #was, xbmc.LOGERROR)
    @property
    def client_key(self):
        key = "123"
        try:
            key = xbmcaddon.Addon().getSetting(self.PAIRING_KEY_PARAMETER_NAME)
            xbmc_log.log("Pairing key read: " + key,xbmc.LOGNOTICE)
            #was, xbmc.LOGDEBUG)
        except:
            xbmc_log.log("Unable to read pairing key",xbmc.LOGNOTICE)
            #, xbmc.LOGERROR)
        return key
    @property
    def register_string(self):
        key = self.client_key
        if key == "":
            register_string = json.JSONEncoder().encode(
                {
                    "type" : "register",
                    "id" : "register_" + str(self._msg_id),
                    "payload" : {
                        "pairingType" : "PROMPT",
                        "manifest" : {
                            "permissions": [
                                "CONTROL_POWER"
                            ]
                        }
                    }
                }
            )
        else:
            register_string = json.JSONEncoder().encode(
                {
                    "type" : "register",
                    "id" : "register_" + str(self._msg_id),
                    "payload" : {
                        "pairingType" : "PROMPT",
                        "client-key" : key,
                        "manifest" : {
                            "permissions": [
                                "CONTROL_POWER"
                            ]
                        }
                    }
                }
            )
        xbmc_log.log("Register string is" + register_string,xbmc.LOGNOTICE)
        #was, xbmc.LOGDEBUG)
        return  register_string
    def opened(self):
        xbmc_log.log("Connection to TV opened",xbmc.LOGNOTICE)
        #was, xbmc.LOGDEBUG)
        self._msg_id = 0
        self.send(self.register_string)
    def closed(self, code, reason=None):
        xbmc_log.log("Connection to TV closed : " + str(code) + "(" + reason + ")",xbmc.LOGNOTICE)
        #was, xbmc.LOGDEBUG)
    def received_message(self, message):
        xbmc_log.log("Message received : (" + str(message) + ")",xbmc.LOGNOTICE)
        #was, xbmc.LOGDEBUG)
        if message.is_text:
            response = json.loads(message.data.decode("utf-8"),"utf-8" )
            if 'client-key' in response['payload']:
                xbmc_log.log("client-key received in response", xbmc.LOGDEBUG)
                xbmc_log.log("so save client-key to addon settings", xbmc.LOGDEBUG)
                self.save_pairing_key(response['payload']['client-key'])
            if response['type'] == 'registered':
                xbmc_log.log("State changed to REGISTERED",xbmc.LOGNOTICE)
                #was, xbmc.LOGDEBUG)
                self._registered = 1
            if self._registered == 0 and response['type'] == 'error':
                xbmc_log.log("Pairing error " + str(response['error']),xbmc.LOGNOTICE)
                #was, xbmc.LOGERROR)
            if self._power_off_sent == 0 and self._registered == 1:
                xbmc_log.log("Sending POWEROFF",xbmc.LOGNOTICE)
                #was, xbmc.LOGDEBUG)
                self.send_power_off()
                self.close()
        else:
            xbmc_log.log("Unreadable message", xbmc.LOGNOTICE)
            #was xbmc.LOGDEBUG)

    def send_power_off(self):
        power_off_string = json.JSONEncoder().encode(
               {
                "type" : "request",
                "id" : "request_" + str(self._msg_id),
                "uri" : "ssap://system/turnOff",
                "payload" : {
                    "client-key" : self.client_key
                }
            }
        )
        self.send(power_off_string)
        self._power_off_sent = 1
        Dialog.notification("LG TV 2015+","Sent command to turn off TV")
        xbmc_log.log("Sent POWEROFF successfully", xbmc.LOGNOTICE)
            #was xbmc.LOGDEBUG)
    @property
    def handshake_headers(self):
        """
        Should overload this, because LG TVs do not operate with Origin correctly
        """
        return [(p, v)
                   for p,v in super(LGTVNetworkShutdown2015,self).handshake_headers
                   if p != "Origin"
               ]
    def __init__(self,ip_address):
        xbmc_log.log("Initiating")
        #######the check has been removed as the TV was not responding to any http/https
        #######if self.check_connection(ip_address):
		#######indent below if I remove the remarks on the if self.check_connection(ip_address): above
        connection_string = 'wss://' + ip_address + ':3001'
        xbmc_log.log("Connection string is [" + connection_string+ "]", xbmc.LOGNOTICE)
        #was xbmc.LOGDEBUG)
        super(LGTVNetworkShutdown2015,self).__init__(connection_string,protocols=['http-only', 'chat'])
        try:
            self.connect()
        except:
            raise RuntimeWarning('Unable to estabilish connection')
            return
        self.run_forever()
        #######else:
        #######    xbmc_log.log("6 check_connection failed " + ip_address,xbmc.LOGNOTICE )
        #######    Dialog.notification("LG TV 2015","Connection failed. Maybe IP or type is incorrect?")
        #######    raise RuntimeWarning('Unable to test connection')
    def check_connection(self, ip_address):
        try:
            connection_url = 'https://' + ip_address + ':3000' #######THis stopped working with a Jan2023 WebOS update
			#Warning - Changing https to http: causes python CRASH!! Error Contents: [Errno 104] Connection reset by peer

            xbmc_log.log("5 Checking https 3000 connection to " + connection_url,xbmc.LOGNOTICE )
            response=urllib2.urlopen(connection_url,timeout=10)
            xbmc_log.log("YEAY! Check passed",xbmc.LOGNOTICE)
            return True
        except urllib2.URLError as err:
            xbmc_log.log("6 https Check failed to "+ connection_url,xbmc.LOGNOTICE)
        return False

#class LGTVNetworkShutdown2011:
    ####### TODO: https://github.com/dreamcat4/lgremote/blob/master/lgremote


if __name__ == '__main__':
    if 'show_help' in sys.argv:
        raise NotImplementedError()
    else:
        #######these were from the BillyNate version that broke kodi CEC control (or just caused screen lockup) that needed a reboot to resolve each time
        #######I do not need to investigate this as I am not really a python programmer.
        #######I would be grateful if anyone could fix this or let me know a soltuion.
        #screensaver_gui = Screensaver("screensaver-display.xml",__path__,"default")
        #screensaver_gui.doModal()
        #del screensaver_gui

        #was previous filimovic version
        networkShutdownScreensaver = LGTVNetworkShutdownScreensaver()
        del networkShutdownScreensaver

        #common to both
        del Addon
        del Dialog
        xbmc_log.log('Screensaver deleted',xbmc.LOGNOTICE)
        xbmc_log.log("--------------screensaver end---------------- " ,xbmc.LOGNOTICE)
        sys.modules.clear()


import urllib,urllib2,re,xbmcplugin,xbmcgui,xbmcaddon, httplib, socket
import sys,os,datetime, time, string, base64, cProfile

__settings__ = xbmcaddon.Addon(id='plugin.video.xonx')
__cwd__ = __settings__.getAddonInfo('path')
BASE_RESOURCE_PATH = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) )
PLUGINPATH=xbmc.translatePath( os.path.join( __cwd__) )
sys.path.append(BASE_RESOURCE_PATH)

import simplejson as json

print "running on " + str(sys.version_info)

#Get the setting from the appropriate file.
print "===== xonx START ====="
g_host = __settings__.getSetting('ipaddress')
g_port = __settings__.getSetting('port')
g_stream = __settings__.getSetting('streaming')
g_secondary = __settings__.getSetting('secondary')
g_debug = __settings__.getSetting('debug')
if g_debug == "true":
    print "xonx -> Settings hostname: " + g_host
    print "xonx -> Settings streaming: " + g_stream
    print "xonx -> Setting secondary: " + g_secondary
    print "xonx -> Setting debug to " + g_debug
else:
    print "xonx -> Debug is turned off.  Running silent"

g_multiple = int(__settings__.getSetting('multiple')) 
g_serverList=[]
if g_multiple > 0:
    if g_debug == "true": print "xonx -> Multiple servers configured; found [" + str(g_multiple) + "]"
    for i in range(1,g_multiple+1):
        if g_debug == "true": print "xonx -> Adding server [Server "+ str(i) +"] at [" + __settings__.getSetting('server'+str(i)) + "]"
        extraip = __settings__.getSetting('server'+str(i))
        if extraip == "":
            if g_debug == "true": print "xonx -> Blank server detected.  Ignoring"
            continue
        try:
            (serverip, port)=extraip.split(':')
        except:
            serverip=extraip
            port="80"
            
        g_serverList.append(['Server '+str(i),serverip, port])

if g_debug == "true": print "xonx -> serverList is " + str(g_serverList)
        
g_proxy = __settings__.getSetting('proxy')
if g_debug == "true": print "xonx -> proxy is " + g_proxy

g_loc = "special://home/addon/plugin.video.xonx"

#Create the standard header structure and load with a User Agent to ensure we get back a response.
g_txheaders = {
              'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US;rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)'	
              }

#Set up the remote access authentication tokens
XBMCInternalHeaders=""
    
g_authentication = __settings__.getSetting('remote')    
if g_authentication == "true":
    if g_debug == "true": print "xonx -> Getting authentication settings."
    g_username= __settings__.getSetting('username')
    g_password =  __settings__.getSetting('password')
    if g_debug == "true": print "xonx -> username is " + g_username
    
    auth = 'Basic ' + string.strip(base64.encodestring(g_username + ':' + g_password))
    g_txheaders['Authorization']=auth
    XBMCInternalHeaders="|Authorization="+urllib.quote_plus(g_txheaders['Authorization'])



################################ Common
# Connect to a server and retrieve the HTML page
def getURL( url ,title="Error", surpress=False, type="GET", urlData=""):
    printDebug("== ENTER: getURL ==")
    try:
        printDebug("url = "+url, getURL.__name__)
        txdata = None
        
        server=url.split('/')[2]
        urlPath="/"+"/".join(url.split('/')[3:])
             
        params = "" 
        conn = httplib.HTTPConnection(server) 
        if type == "POST":
                conn.request("POST", urlPath, urlData, headers=g_txheaders) 
        else:
                conn.request("GET", urlPath, headers=g_txheaders) 
        data = conn.getresponse() 
        if int(data.status) >= 400:
            error = "HTTP response error: " + str(data.status) + " " + str(data.reason)
            if surpress is False:
                xbmcgui.Dialog().ok(title,error)
            print error
            return False
        else:      
            link=data.read()
            printDebug("====== XML returned =======",getURL.__name__)
            printDebug(link)
            printDebug("====== XML finished ======",getURL.__name__)
    except socket.gaierror :
        error = 'Unable to lookup host: ' + server + "\nCheck host name is correct"
        if surpress is False:
            xbmcgui.Dialog().ok(title,error)
        print error
        return False
    except socket.error, msg : 
        error="Unable to connect to " + server +"\nReason: " + str(msg)
        if surpress is False:
            xbmcgui.Dialog().ok(title,error)
        print error
        return False
    else:
        return link

def printDebug(msg,functionname=""):
    if g_debug == "true":
        if functionname == "":
            print str(msg)
        else:
            print "xonx -> " + str(functionname) + ": " + str(msg)
 
#Used to add playable media files to directory listing
#properties is a dictionary {} which contains a list of setInfo properties to apply
#Arguments is a dictionary {} which contains other arguments used in teh creation of the listing (such as name, resume time, etc)
def addLink(url,properties,arguments):
        printDebug("== ENTER: addLink ==")
        try:
            printDebug("Adding link for [" + properties['title'] + "]", addLink.__name__)
        except: pass
        printDebug("Passed arguments are " + str(arguments), addLink.__name__)
        printDebug("Passed properties are " + str(properties), addLink.__name__)
        
        try:
            type=arguments['type']
        except:
            type='Video'
            
        if type =="Picture":
             u=url
        else:
            u=sys.argv[0]+"?url="+str(url)
        
        ok=True
        
        printDebug("URL to use for listing: " + u, addLink.__name__)
        #Create ListItem object, which is what is displayed on screen
        try:
            liz=xbmcgui.ListItem(properties['title'], iconImage=arguments['thumb'], thumbnailImage=arguments['thumb']+XBMCInternalHeaders)
            printDebug("Setting thumbnail as " + arguments['thumb'],addLink.__name__)              
        except:
            liz=xbmcgui.ListItem(properties['title'], iconImage='', thumbnailImage='')
            
        #Set properties of the listitem object, such as name, plot, rating, content type, etc
        liz.setInfo( type=type, infoLabels=properties ) 
        
        try:
            liz.setProperty('Artist_Genre', properties['genre'])
            liz.setProperty('Artist_Description', properties['plot'])
        except: pass

        
        #Set the file as playable, otherwise setresolvedurl will fail
        liz.setProperty('IsPlayable', 'true')
                
        #Set the fanart image if it has been enabled
        try:
            liz.setProperty('fanart_image', str(arguments['fanart_image']+XBMCInternalHeaders))
            printDebug( "Setting fan art as " + str(arguments['fanart_image']),addLink.__name__)
        except: pass
        
        #Finally add the item to the on screen list, with url created above
        ok=xbmcplugin.addDirectoryItem(handle=pluginhandle,url=u,listitem=liz)
        
        return ok

#Used to add directory item to the listing.  These are non-playable items.  They can be mixed with playable items created above.
#properties is a dictionary {} which contains a list of setInfo properties to apply
#Arguments is a dictionary {} which contains other arguments used in teh creation of the listing (such as name, resume time, etc)
def addDir(url,properties,arguments):
        printDebug("== ENTER: addDir ==")
        try:
            printDebug("Adding Dir for [" + properties['title'] + "]", addDir.__name__)
        except: pass

        printDebug("Passed arguments are " + str(arguments), addDir.__name__)
        printDebug("Passed properties are " + str(properties), addDir.__name__)
        
        #Create the URL to pass to the item
        u=sys.argv[0]+"?url="+str(url)
        ok=True
                
        #Create the ListItem that will be displayed
        try:
            liz=xbmcgui.ListItem(properties['title'], iconImage=arguments['thumb'], thumbnailImage=arguments['thumb']+XBMCInternalHeaders)
            printDebug("Setting thumbnail as " + arguments['thumb'],addDir.__name__)
        except:
            liz=xbmcgui.ListItem(properties['title'], iconImage='', thumbnailImage='')
        
            
        #Set the properties of the item, such as summary, name, season, etc
        try:
            liz.setInfo( type=arguments['type'], infoLabels=properties ) 
        except:
            liz.setInfo(type='Video', infoLabels=properties ) 

        printDebug("URL to use for listing: " + u, addDir.__name__)
        
        try:
            liz.setProperty('Artist_Genre', properties['genre'])
            liz.setProperty('Artist_Description', properties['plot'])
        except: pass
        
        #If we have set a number of watched episodes per season
        try:
            #Then set the number of watched and unwatched, which will be displayed per season
            liz.setProperty('WatchedEpisodes', str(arguments['WatchedEpisodes']))
            liz.setProperty('UnWatchedEpisodes', str(arguments['UnWatchedEpisodes']))
        except: pass
        
        #Set the fanart image if it has been enabled
        try:
            liz.setProperty('fanart_image', str(arguments['fanart_image']+XBMCInternalHeaders))
            printDebug( "Setting fan art as " + str(arguments['fanart_image']),addDir.__name__)
        except: pass

        #Finally add the item to the on screen list, with url created above
        ok=xbmcplugin.addDirectoryItem(handle=pluginhandle,url=u,listitem=liz,isFolder=True)
        return ok

################################ Root listing
# Root listing is the main listing showing all sections.  It is used when these is a non-playable generic link content
def ROOT():
        printDebug("== ENTER: ROOT() ==")
        xbmcplugin.setContent(pluginhandle, 'movies')

        #Get the global host variable set in settings
        host=g_host
        
        Servers=[]
      
        #If we have a remote host, then don;t do local discovery as it won't work
        Servers.append(["Main",g_host, g_port])
        Servers += g_serverList
        #For each of the servers we have identified
        for server in Servers:
                                      
            
            arguments={}
            properties={}
            arguments['title']="Movies"

            try:
                if g_multiple == 0:
                    properties['title']=arguments['title']
                else:
                    properties['title']=server[0]+": "+arguments['title']
            except:
                properties['title']="unknown"
                
            arguments['type']="Video"
            mode=2    
            s_url='http://'+server[1]+':'+server[2]+"/jsonrpc&mode="+str(mode)                
            
            #Build that movies listing..
            addDir(s_url, properties,arguments)
            
            arguments['title']="TV Shows"
            try:
                if g_multiple == 0:
                    properties['title']=arguments['title']
                else:
                    properties['title']=server[0]+": "+arguments['title']
            except:
                properties['title']="unknown"
                
            arguments['type']="Video"

            mode=1
            s_url='http://'+server[1]+':'+server[2]+"/jsonrpc&mode="+str(mode)
                
            #Build that movies listing..
            addDir(s_url, properties,arguments)
            
        #All XML entries have been parsed and we are ready to allow the user to browse around.  So end the screen listing.
        xbmcplugin.endOfDirectory(pluginhandle)  
################################ Movies listing            
# Used to display movie on screen.

def Movies(url):
        printDebug("== ENTER: movies() ==")
        xbmcplugin.setContent(pluginhandle, 'movies')
        win=xbmcgui.getCurrentWindowId()
        WINDOW=xbmcgui.Window(win)
        WINDOW.setProperty("xonx.type", "movies")
        
        server=url.split('/')[2]

        #Get some data and parse it
        string=json.dumps({"method":"VideoLibrary.GetMovies","id":"1","jsonrpc":"2.0", "params":{"fields":["title","fanart","file","country","director","genre","imdbnumber","lastplayed", "mpaa", "originaltitle","playcount", "plot", "plotoutline","premiered", "productioncode","rating", "runtime", "set", "showlink", "streamDetails", "studio", "tagline", "thumbnail", "top250","trailer","votes", "writer", "writingcredits","year", "cast"]}})
            
        html=getURL(url, type="POST", urlData=string)
            
        if html is False:
            return
               
        help=json.loads(html)
        results=help['result']
        print str(results)
        try:
            if results['limits']['total'] == 0:
                xbmcgui.Dialog().ok("Error","No library entries found")
                return
        except:
            if results['total'] == 0:
                xbmcgui.Dialog().ok("Error","No library entries found")
                return
            
        movieTags=results['movies']
                   
        #Find all the video tags, as they contain the data we need to link to a file.
        for movie in movieTags:
            
            print str(movie)
            printDebug("---New Item---", Movies.__name__)
            arguments={}
            properties=dict(movie.items())
            
            #Get the watched status
            try:
                if properties['playcount'] > 0:
                    properties['overlay']=7
            except: 
                properties['overlay']=6
            
            arguments['viewoffset']=0
                        
           
            #Get the picture to use
            try:
                arguments['thumb']='http://'+server+"/vfs/"+urllib.quote_plus(properties['thumbnail'])
            except:
                pass
               
            #Get a nice big picture  
            try:
                art_url="http://"+server+"/vfs/"+urllib.quote_plus(properties['fanart'])
            except:
                art_url=""

            arguments['fanart_image']=art_url

            #Ensure that the file name is encoded too...
            properties['file']=properties['file'].encode('utf-8')

            try:
                protocol=properties['file'].split(':')[0]
                printDebug ("Protocol for media is " + protocol, Movies.__name__)
                if len(protocol) <= 2:
                    properties['file']="http://"+server+"/vfs/"+urllib.quote_plus(properties['file'])
                    printDebug ("local file detected, setting to VFS location: " + properties['file'], Movies.__name__)
            except: pass
            #Set type
            arguments['type']="Video"
            
            
            #This is playable media, so link to a path to a play function
            mode=12
                             
            u=properties['file']+"&mode="+str(mode)
                     
            #Right, add that link...and loop around for another entry
            addLink(u,properties,arguments)        
        
        #If we get here, then we've been through the XML and it's time to finish.
        xbmcplugin.endOfDirectory(pluginhandle)

def convert(data):
    if isinstance(data, unicode):
        return str(data)
    elif isinstance(data, dict):
        return dict(map(convert, data.iteritems()))
    elif isinstance(data, (list, tuple, set, frozenset)):
        return type(data)(map(convert, data))
    else:
         return data
         
################################ TV Show Listings
#This is the function use to parse the top level list of TV shows
def SHOWS(url=''):
        printDebug("== ENTER: SHOWS() ==")
        xbmcplugin.setContent(pluginhandle, 'tvshows')

        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
        
        win=xbmcgui.getCurrentWindowId()
        WINDOW=xbmcgui.Window(win)
        WINDOW.setProperty("xonx.type", "tvshows")

        #Get the URL and server name.  Get the XML and parse
        server=url.split('/')[2]

        string=json.dumps({"method":"VideoLibrary.GetTVShows","id":"1","jsonrpc":"2.0", "params":{"fields":["title","episode","fanart","file","genre","imdbnumber","lastplayed","mpaa","playcount","plot","premiered","rating","studio","thumbnail","votes","year"]}})

        html=getURL(url, type="POST", urlData=string )
        
        if html is False:
            return

        help=json.loads(html)
        results=help['result']
        try:
            if results['limits']['total'] == 0:
                xbmcgui.Dialog().ok("Error","No library entries found")
                return
        except:
            if results['total'] == 0:
                xbmcgui.Dialog().ok("Error","No library entries found")
                return

        ShowTags=results['tvshows']
            
        #For each directory tag we find
        for show in ShowTags:

            properties=dict(show.items())
            arguments={}
            
            #Get the picture to use
            try:
                arguments['thumb']='http://'+server+"/vfs/"+urllib.quote_plus(properties['thumbnail'])
            except:
                pass
               
            #Get a nice big picture  
            try:
                art_url="http://"+server+"/vfs/"+urllib.quote_plus(properties['fanart'])
            except:
                art_url=""

            arguments['fanart_image']=art_url

           
            #Set type
            arguments['type']="Video"

            properties['tvshowid']=str(properties['tvshowid'])
            
            mode=4 # grab season details
            tv_url=url+"&mode="+str(mode)+"&id="+str(properties['tvshowid'])
            
            addDir(tv_url,properties,arguments) 
            
        #End the listing    
        xbmcplugin.endOfDirectory(pluginhandle)
 
################################ TV Season listing            
#Used to display the season data         
def Seasons(url,id):
        printDebug("== ENTER: season() ==")
        xbmcplugin.setContent(pluginhandle, 'seasons')

        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
        win=xbmcgui.getCurrentWindowId()
        WINDOW=xbmcgui.Window(win)
        WINDOW.setProperty("xonx.type", "seasons")

        #Get URL, XML and parse
        server=url.split('/')[2]
        print server
        print id
        string=json.dumps({"method":"VideoLibrary.GetSeasons","id":"1","jsonrpc":"2.0", "params": {"tvshowid":int(id), "fields":["episode","fanart","playcount","season","showtitle","thumbnail"]}})

        html=getURL(url, type="POST", urlData=string )
        
        if html is False:
            return

        help=json.loads(html)
        results=help['result']
        try:
            if results['limits']['total'] == 0:
                xbmcgui.Dialog().ok("Error","No library entries found")
                return
        except:
            if results['total'] == 0:
                xbmcgui.Dialog().ok("Error","No library entries found")
                return
            

        ShowTags=results['seasons']
        for show in ShowTags:
        
            arguments={}
            properties=dict(show.items());
            #Build basic data structures
 
            #Get the picture to use
            try:
                arguments['thumb']='http://'+server+"/vfs/"+urllib.quote_plus(properties['thumbnail'])
            except:
                pass
               
            #Get a nice big picture  
            try:
                art_url="http://"+server+"/vfs/"+urllib.quote_plus(properties['fanart'])
            except:
                art_url=""

            arguments['fanart_image']=art_url

            properties['title']=properties['label']

            #Set type
            arguments['type']="Video"

            #Set the mode to episodes, as that is what's next     
            mode=6
            u=url+"&mode="+str(mode)+"&id="+id+":"+str(properties['season'])
        
            #Build the screen directory listing
            addDir(u,properties,arguments) 
            
        #All done, so end the listing
        xbmcplugin.endOfDirectory(pluginhandle)
 
################################ TV Episode listing 
#Displays the actual playable media
def EPISODES(url,id):
        printDebug("== ENTER: EPISODES() ==")
        xbmcplugin.setContent(pluginhandle, 'episodes')
        
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_EPISODE)
        win=xbmcgui.getCurrentWindowId()
        WINDOW=xbmcgui.Window(win)
        WINDOW.setProperty("xonx.type", "episodes")

        #split the tvid/season variable
        (tvid, seasonid) = id.split(':')
       
        #Get the server
        server=url.split('/')[2]
        string=json.dumps({"method":"VideoLibrary.GetEpisodes","id":"1","jsonrpc":"2.0", "params": {"tvshowid":int(tvid), "season":int(seasonid), "fields":["cast","director","episode","fanart","file","firstaired","lastplayed","originaltitle","playcount","plot","productioncode","rating","runtime","season","showtitle","streamDetails","thumbnail","title","votes","writingcredits"]}}) 

        html=getURL(url, type="POST", urlData=string )
        
        if html is False:
            return

        help=json.loads(html)
        results=help['result']
        try:
            if results['limits']['total'] == 0:
                xbmcgui.Dialog().ok("Error","No library entries found")
                return
        except:
            if results['total'] == 0:
                xbmcgui.Dialog().ok("Error","No library entries found")
                return
            
        
        ShowTags=results['episodes']
        
        for show in ShowTags:
                      
            arguments={}
            properties=dict(show.items())
                       
            #Get the watched status
            try:
                properties['playcount']=int(arguments['viewCount'])
                if properties['playcount'] > 0:
                    properties['overlay']=7
            except: pass
            
            #Get the last played position  
            try:
                arguments['viewOffset']=int(arguments['viewOffset'])/1000
            except:
                arguments['viewOffset']=0

                        
            #If we are processing an "All Episodes" directory, then get the season from the video tag              
            try:
                arguments['thumb']='http://'+server+"/vfs/"+urllib.quote_plus(properties['thumbnail'])
            except:
                pass
               
            #Get a nice big picture  
            try:
                art_url="http://"+server+"/vfs/"+urllib.quote_plus(properties['fanart'])
            except:
                art_url=""

            arguments['fanart_image']=art_url

            try:
                protocol=properties['file'].split(':')[0]
                printDebug ("Protocol for media is " + protocol, Movies.__name__)
                if len(protocol) <= 2:
                    properties['file']="http://"+server+"/vfs/"+urllib.quote_plus(properties['file'])
                    printDebug ("local file detected, setting to VFS location: " + properties['file'], Movies.__name__)
            except: pass


            #Set type
            arguments['type']="Video"

            #If we are streaming, then get the virtual location
            #Set mode 5, which is play            
            mode=12

            u=str(properties['file'])+"&mode="+str(mode)
                
            #Build a file link and loop
            addLink(u,properties,arguments)        
        
        #End the listing
        xbmcplugin.endOfDirectory(pluginhandle)

#Just a standard playback 
def PLAY(vids):
        printDebug("== ENTER: PLAY ==")
        #This is for playing standard non-PMS library files (such as Plugins)
        protocol=vids.split(':')[0]
        printDebug ("Protocol for media is " + protocol, PLAY.__name__)
        if protocol == "http":
            url = vids+XBMCInternalHeaders
        else:
            url=vids
        item = xbmcgui.ListItem(path=url)
        return xbmcplugin.setResolvedUrl(pluginhandle, True, item)
        
#Function to parse the arguments passed to the plugin..
def get_params():
        printDebug("== ENTER: get_params ==")
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                #Rather than replace ? with ' ' - I split of the first char, which is always a ? (hopefully)
                #Could always add a check as well..
                cleanedparams=params[1:] #.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        #Right, extended urls that contain = do not parse correctly and this tops plugins from working
                        #Need to think of a better way to do the split, at the moment i'm hacking this by gluing the
                        #two bits back togethers.. nasty...
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                        elif (len(splitparams))==3:
                                param[splitparams[0]]=splitparams[1]+"="+splitparams[2]
                                
        return param

def skin():
    return
   
##So this is where we really start the plugin.

print "Script argument is " + str(sys.argv[1])
if str(sys.argv[1]) == "skin":
    skin()
else:
    pluginhandle = int(sys.argv[1])

    #first thing, parse the arguments, as this has the data we need to use.              
    params=get_params()
    if g_debug == "true": print "xonx -> " + str(params)

    #Set up some variables
    url=None
    name=None
    mode=None
    resume=None
    id=None
    duration=None

    #Now try and assign some data to them
    try:
            #url=urllib.unquote_plus(params["url"])
            url=params['url']
    except:
            pass
    try:
            name=urllib.unquote_plus(params["name"])
    except:
            pass
    try:
            mode=int(params["mode"])
    except:
            pass
    try:
            resume=int(params["resume"])
    except:
            resume=0
    try:
            id=params["id"]
    except:
            pass
    try:
            duration=params["duration"]
    except:
            duration=0
            
    if g_debug == "true":
        print "xonx -> Mode: "+str(mode)
        print "xonx -> URL: "+str(url)
        print "xonx -> Name: "+str(name)
        print "xonx -> ID: "+ str(id)
        print "xonx -> Duration: " + str(duration)

    #Run a function based on the mode variable that was passed in the URL

    if mode!=5:
        __settings__.setSetting('resume', '')

    if mode==None or url==None or len(url)<1:
            ROOT()
    elif mode==1:
            SHOWS(url)
    elif mode==2:
            Movies(url)
    elif mode==4:
            Seasons(url,id)
    elif mode==6:
            EPISODES(url,id)
    elif mode==12:
            PLAY(url)


print "===== xonx STOP ====="
   
#clear done and exit.        
sys.modules.clear()

from pynput import keyboard
from datetime import datetime
import vlc,sys,time,json,logging
from obswebsocket import obsws, requests


# load variables from config
def get_config(r,config):
    result = r[r.find(config+"=")+len(config)+1:]
    result = result[:result.find("\n")]
    return result
with open("./config.cfg","r") as file:
    a = file.read()
    host = get_config(a,"obsHost")
    port = get_config(a,"obsPort")
    password = get_config(a,"obsPassword")
    exitKey = get_config(a,"exitKey")
    packName = get_config(a,"packName")
    debugMode = get_config(a,"debugMode")

# enable websocket logging
if debugMode in ["true","1","True"]:
    logging.basicConfig(level=logging.DEBUG)
sys.path.append('./')

# load pack
packPath = "./packs/"+packName
with open(packPath+'/'+"data.json","r") as file:
    jsonData = json.loads(file.read())
    originalScene=jsonData['originalScene']
    combos = jsonData['combos']

# load sounds
sounds = list()
for i in combos:
    sounds.append(vlc.MediaPlayer(packPath+'/'+i["soundName"]))


buttons = {"a":"1","s":"2","z":"3","x":"4",
           "Key.left":"b","Key.right":"f","Key.up":"u","Key.down":"d"}

diagonals = {
    ("b","d"):"db", 
    ("b","u"):"ub", 
    ("f","d"):"df", 
    ("f","u"):"uf", 
    }
punches = {
    ("1","2"):"1+2",
    ("1","3"):"1+3",
    ("1","4"):"1+4",
    ("2","3"):"2+3",
    ("2","4"):"2+4",
    ("3","4"):"3+4",

    ("2","3","4"):"2+3+4",
    ("3","2","4"):"2+3+4",
    ("2","4","3"):"2+3+4",
    }

begin=datetime.now().timestamp()
frame=0 #this is not FPS!!! just ticks

buffer = []
movePressed = set()
pressed = set()
complete = -1
def on_press(key):
    global frame,begin,buffer,movePressed,pressed
    frame=datetime.now().timestamp()-begin
    begin=datetime.now().timestamp()    
    if frame >=0.5:
        buffer = []
        movePressed = set()
        pressed = set()
    try:
        #print('alphanumeric key {0} pressed'.format(
        #    key.char),str(round(frame,2)))
        
        if key.char in buttons:
            pressed.add(buttons[key.char])

        # if had two buttons combination
        if tuple(pressed) in punches.keys():
            buffer=buffer[:len(buffer)-len(pressed)+1]
            buffer.append(punches[tuple(pressed)])
        elif tuple(pressed)[::-1] in punches.keys():
            buffer=buffer[:len(buffer)-len(pressed)+1]
            buffer.append(punches[tuple(pressed)[::-1]])
        # otherwise
        else:
            buffer.append(buttons[key.char])
    except Exception:#AttributeError:
        #print('special key {0} pressed'.format(
        #    key),str(round(frame,2)))
        if str(key) in buttons:
            movePressed.add(buttons[str(key)])
            # if diagonal pressed
            if tuple(movePressed) in diagonals.keys():
                buffer.append(diagonals[tuple(movePressed)])
            elif tuple(movePressed)[::-1] in diagonals.keys():
                buffer.append(diagonals[tuple(movePressed)[::-1]])
            # otherwise
            else:
                buffer.append(buttons[str(key)])

# test b+1
def test_combo():
    global buffer,complete,combos
    for j in range(len(combos)):
        combo = combos[j]["combo"][0]
        if len(buffer) < len(combo):
            continue
        cmp = True
        for i in range(len(combo)):
            cmp = ((combo[i]==buffer[i]) or (combo[i]=="#")) and cmp
        if cmp:
            complete = j
            return cmp
        
    return False

ex=False
def on_release(key):
    global ex,buffer
    #print('{0} released'.format(
    #    key))
    try:
        if key.char in buttons:
            pressed.remove(buttons[key.char])
    except:
        if str(key) in buttons:
            try:
                movePressed.remove(buttons[str(key)])
            except:
                pass
            if len(movePressed)==1:
                buffer.append(tuple(movePressed)[0])
    #print(movePressed)
    #print(buffer)
    if test_combo():
        buffer = []
        # Stop listener
        return False
    elif str(key) == exitKey:
        ex=True
        return False

# Collect events until released



ws = obsws(host, port, password)
ws.connect()
        
while True:
    with keyboard.Listener(
            on_press=on_press,
            on_release=on_release
            ) as listener:
        try:
            listener.join()
        except Exception as e:
            print(e.args[0])

    if ex==True:
        ws.disconnect()
        sys.exit()

    try:
#        scenes = ws.call(requests.GetSceneList())
#        for s in scenes.getScenes():
#            name = s['sceneName']
#            print("Switching to {}".format(name))
        ws.call(requests.SetCurrentProgramScene(sceneName=combos[complete]["scene"]))
        for sound in sounds:
            sound.stop()
        sounds[complete].play()

        time.sleep(0.5)
        ws.call(requests.SetCurrentProgramScene(sceneName="game"))
        complete=-1
        
        #print("complete")

    except KeyboardInterrupt:
        pass

ws.disconnect()


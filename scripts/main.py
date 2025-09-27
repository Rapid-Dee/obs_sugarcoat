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
    obsEnabled = get_config(a,"OBS_ENABLED")
    
    host = get_config(a,"OBS_HOST")
    port = get_config(a,"OBS_PORT")
    password = get_config(a,"OBS_PASSWORD")
    inputType = get_config(a,"INPUT_TYPE")
    exitKey = get_config(a,"EXIT_KEY")
    packName = get_config(a,"PACK_NAME")
    debugMode = get_config(a,"DEBUG_MODE")
    buttons = {
        get_config(a,"KEY_UP"):"u",
        get_config(a,"KEY_DOWN"):"d",
        get_config(a,"KEY_LEFT"):"b",
        get_config(a,"KEY_RIGHT"):"f",
        get_config(a,"KEY_1"):"1",
        get_config(a,"KEY_2"):"2",
        get_config(a,"KEY_3"):"3",
        get_config(a,"KEY_4"):"4"
        }

if inputType == "keyboard":
    from pynput import keyboard

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



diagonals = {
    ("u","b"):"ub", 
    ("d","b"):"db", 
    ("u","f"):"uf", 
    ("d","f"):"df", 
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

complete = -1
buffer = []
movePressed = set()
pressed = set()
ex=False

if inputType=="keyboard":
    def on_press(key):
        global frame,begin,buffer,movePressed,pressed
        frame=datetime.now().timestamp()-begin
        begin=datetime.now().timestamp()    
        if frame >=0.5:
            buffer = []
            movePressed = set()
            pressed = set()
        try:
            btn = key.char   
        except Exception:#AttributeError:
            btn = str(key)

        if debugMode in ["True","1","true"]:
            print(btn,str(round(frame,2)))
            print(movePressed,buffer,"\n")
        
        if btn in buttons.keys():
            if buttons[btn] in "udbf":
                movePressed.add(buttons[btn])
                if frame<=0.05:
                    buffer = buffer[:-1]
                # if diagonal pressed
                if tuple(movePressed) in diagonals.keys():
                    buffer.append(diagonals[tuple(movePressed)])
                elif tuple(movePressed)[::-1] in diagonals.keys():
                    buffer.append(diagonals[tuple(movePressed)[::-1]])
                # otherwise
                else:
                    buffer.append(buttons[btn])
            if buttons[btn] in "1234":
                pressed.add(buttons[btn])

                # if had two buttons combination
                if tuple(pressed) in punches.keys():
                    buffer=buffer[:len(buffer)-len(pressed)+1]
                    buffer.append(punches[tuple(pressed)])
                elif tuple(pressed)[::-1] in punches.keys():
                    buffer=buffer[:len(buffer)-len(pressed)+1]
                    buffer.append(punches[tuple(pressed)[::-1]])
                # otherwise
                else:
                    buffer.append(buttons[btn])

    def test_combo():
        global buffer,complete,combos
        for j in range(len(combos)):
            combo = combos[j]["combo"]
            if len(buffer) < len(combo):
                continue
            cmp = True
            cnt = 0
            for i in range(-1,-len(combo)+1,-1):
                cmp = ((combo[i]==buffer[i]) or (combo[i]=="#")) and cmp
            if cmp:
                complete = j
                return cmp
        return False

    def on_release(key):
        global ex,buffer,movePressed
        if debugMode in ["True","1","true"]:
            print(movePressed,buffer,"\n")
        
        
        try:
            btn = key.char
        except:
            btn = str(key)
        if btn in buttons:
            if buttons[btn] in "udbf":
                try:
                    movePressed.remove(buttons[btn])
                except:
                    pass
                if len(movePressed)==1:
                    buffer.append(tuple(movePressed)[0])
                #if frame<=0.05 and (buffer[-1] in "f","u","d","b"):
                #    buffer = buffer[:-1]
            if buttons[btn] in "1234":
                pressed.remove(buttons[btn])
        if test_combo():
            buffer = []
             # Stop listener
            return False
        elif str(key) == exitKey:
            ex=True
            return False

    # Collect events until released



if obsEnabled in ["true","1","True"]:
    ws = obsws(host, port, password)
    ws.connect()
        
while True:
    if inputType=="keyboard":
        with keyboard.Listener(
                on_press=on_press,
                on_release=on_release
                ) as listener:
            try:
                listener.join()
            except Exception as e:
                print(e.args[0])

    if ex==True:
        if obsEnabled in ["true","1","True"]:
            ws.disconnect()
        sys.exit()

    try:
#        scenes = ws.call(requests.GetSceneList())
#        for s in scenes.getScenes():
#            name = s['sceneName']
#            print("Switching to {}".format(name))
        if obsEnabled in ["true","1","True"]:
            ws.call(requests.SetCurrentProgramScene(sceneName=combos[complete]["scene"]))
        
        sounds = list()
        for i in combos:
            sounds.append(vlc.MediaPlayer(packPath+'/'+i["soundName"]))
        for sound in sounds:
            sound.stop()
        sounds[complete].play()
        

        if obsEnabled in ["true","1","True"]:
            time.sleep(0.1)
            ws.call(requests.SetCurrentProgramScene(sceneName=originalScene))
        print("Playing "+combos[complete]["soundName"])
        complete=-1
        buffer=[]
        

    except KeyboardInterrupt:
        pass
if obsEnabled in ["true","1","True"]:
    ws.disconnect()


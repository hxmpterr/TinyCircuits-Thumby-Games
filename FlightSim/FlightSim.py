#### !!!! BLOCKLY EXPORT !!!! ####
from thumbySprite import Sprite
from thumbyGraphics import display
import time
Number = int
import thumbyButton as buttons
from thumbyAudio import audio

start = None
plane = None
plane2 = None
planeleft = None
planeright = None
planedown = None
planeup = None
cloud = None
cloud2 = None
home = None
mountains = None
cloudy = None
couldy2 = None
mountainX = None
mountainy = None

plane = Sprite(1,1,bytearray([1]))

plane2 = Sprite(1,1,bytearray([1]))

planeleft = Sprite(1,1,bytearray([1]))

planeright = Sprite(1,1,bytearray([1]))

planedown = Sprite(1,1,bytearray([1]))

planeup = Sprite(1,1,bytearray([1]))

cloud = Sprite(1,1,bytearray([1]))

cloud2 = Sprite(1,1,bytearray([1]))

home = Sprite(1,1,bytearray([1]))

mountains = Sprite(1,1,bytearray([1]))

def __print_to_display__(message):
      message = str(message)
      display.fill(0)
      txt = [""]
      for line in message.split("\n"):
          for word in line.split(" "):
              next_len = len(txt[-1]) + len(word) + 1
              if next_len*display.textWidth + (next_len-1) > display.width:
                  txt += [""]
              txt[-1] += (" " if txt[-1] else "") + word
          txt += [""]
      for ln, line in enumerate(txt):
          display.drawText(line, 0, (display.textHeight+1)*ln, 1)
      display.display.show()



start = 0
plane = Sprite(16,8,bytearray([0,0,4,28,76,108,126,127,126,108,76,28,4,0,0,0]), plane.x,plane.y,plane.key,plane.mirrorX,plane.mirrorY)
plane2 = Sprite(16,8,bytearray([0,0,4,28,76,108,127,127,127,108,76,28,4,0,0,0]), plane2.x,plane2.y,plane2.key,plane2.mirrorX,plane2.mirrorY)
planeleft = Sprite(16,8,bytearray([0,0,59,31,78,127,63,25,12,6,0,0,0,0,0,0]), planeleft.x,planeleft.y,planeleft.key,planeleft.mirrorX,planeleft.mirrorY)
planeright = Sprite(16,8,bytearray([0,0,0,0,0,0,6,12,25,59,126,110,15,50,0,0]), planeright.x,planeright.y,planeright.key,planeright.mirrorX,planeright.mirrorY)
planedown = Sprite(16,8,bytearray([0,0,12,28,24,25,155,255,255,155,25,24,28,12,0,0]), planedown.x,planedown.y,planedown.key,planedown.mirrorX,planedown.mirrorY)
planeup = Sprite(16,8,bytearray([0,0,24,28,12,12,157,255,255,157,12,12,28,24,0,0]), planeup.x,planeup.y,planeup.key,planeup.mirrorX,planeup.mirrorY)
cloud = Sprite(16,8,bytearray([56,108,196,130,129,129,129,130,130,66,65,193,131,132,152,96]), cloud.x,cloud.y,cloud.key,cloud.mirrorX,cloud.mirrorY)
cloud2 = Sprite(16,8,bytearray([56,108,70,66,98,52,34,65,97,35,18,19,17,11,6,0]), cloud2.x,cloud2.y,cloud2.key,cloud2.mirrorX,cloud2.mirrorY)
home = Sprite(32,32,bytearray([0,0,0,0,0,0,0,0,0,0,0,0,32,160,96,96,160,32,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
            0,0,240,72,72,72,72,68,68,68,68,68,71,248,68,68,248,71,68,68,68,68,68,72,72,72,72,240,0,0,0,0,
            0,0,0,1,1,1,1,2,2,130,194,98,39,249,0,0,249,39,98,194,130,2,2,1,1,1,1,0,0,0,0,0,
            0,0,0,0,0,0,0,0,3,2,2,2,2,3,4,4,3,2,2,2,2,3,0,0,0,0,0,0,0,0,0,0]), home.x,home.y,home.key,home.mirrorX,home.mirrorY)
mountains = Sprite(144,8,bytearray([252,252,252,248,240,240,240,240,192,192,224,224,240,248,248,252,248,224,192,192,192,224,224,240,240,248,240,192,224,224,240,248,248,248,248,248,240,240,224,192,192,192,192,128,128,128,128,192,192,224,240,240,240,224,224,192,128,128,128,128,192,192,192,224,224,224,240,240,240,240,240,240,224,224,192,192,192,192,192,192,192,224,224,224,240,240,240,240,224,192,192,192,192,224,224,240,240,240,240,240,240,248,248,252,252,252,254,250,252,252,248,240,192,192,192,192,192,192,192,224,224,224,240,240,240,240,240,224,224,224,192,192,192,224,224,240,248,248,248,252,252,252,252,252]), mountains.x,mountains.y,mountains.key,mountains.mirrorX,mountains.mirrorY)
cloud.x = 15
cloud.y = -5
cloud2.x = 45
cloud2.y = -5
mountains.x = -30
mountains.y = 20
plane.x = 30
plane.y = 8
plane2.x = 30
plane2.y = 8
planedown.x = 30
planedown.y = 8
planeup.x = 30
planeup.y = 4
planeleft.x = 25
planeleft.y = 8
planeright.x = 35
planeright.y = 8
while start != 1:
  home.x = 43
  home.y = 17
  display.setFont("/lib/font3x5.bin", 3, 5, display.textSpaceWidth)
  __print_to_display__('FlightSim Made By')
  display.drawText(str('CDIMENSIONAL'), 1, 12, 1)
  display.drawSprite(home)
  display.update()
  time.sleep(3)
  start = (start if isinstance(start, Number) else 0) + 1
while True:
  cloudy = cloud.y
  couldy2 = cloud2.y
  mountainX = mountains.x
  mountainy = mountains.y
  display.fill(0)
  display.drawSprite(mountains)
  if cloudy > 20:
    cloud.x = 15
    cloud.y = -5
  if couldy2 > 20:
    cloud2.x = 45
    cloud2.y = -5
  if buttons.buttonL.pressed():
    audio.play(100, 1000)
    display.drawSprite(planeleft)
    mountains.x += 0.2
    display.update()
  if buttons.buttonR.pressed():
    audio.play(100, 1000)
    display.drawSprite(planeright)
    mountains.x += -0.2
    display.update()
  if buttons.buttonR.pressed():
    audio.play(100, 1000)
    display.drawSprite(planeright)
    mountains.x += -0.2
    display.update()
  if buttons.buttonU.pressed():
    audio.play(100, 1000)
    display.drawSprite(planeup)
    mountains.y += 0.1
    display.update()
  if buttons.buttonD.pressed():
    audio.play(100, 1000)
    display.drawSprite(planedown)
    mountains.y += -0.1
    display.update()
  if not buttons.inputPressed():
    audio.play(80, 1000)
    display.drawSprite(plane)
    display.update()
    display.drawSprite(plane2)
    display.update()
  if mountainX < -70:
    mountains.x = -30
  if mountainX > 0:
    mountains.x = -30
  if mountainy < 6:
    audio.play(300, 300)
    __print_to_display__('YOU CRASHED')
    time.sleep(1.5)
    mountains.x = -30
    mountains.y = 20
    __print_to_display__('Restarting...')
    time.sleep(1.5)
  display.drawSprite(cloud)
  cloud.x += -0.1
  cloud.y += 0.1
  display.drawSprite(cloud2)
  cloud2.x += 0.1
  cloud2.y += 0.2
  display.update()

#### !!!! BLOCKLY EXPORT !!!! ####
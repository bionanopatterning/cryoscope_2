import numpy as np
from Utility import *
#
dev_sim = True
#
dt = 0.0
magnification = 100
pixelSize = 6.5 # micron
numPixels = 2048
xyStageAngle = 135.0
# Date and time upon startup
workingDirectory = "C:/Users/mgflast/Desktop/cryoscope_data"

acquisitionNotes = "..."
snapSaveTitle = "snap_"
autoSaveSnap = False
notes_bufferSize = 2000
cryostage_status = "idle"
cryostage_temperatures = [100, 100, 100]
cryostage_temperature_high_warnings = [-190, -165, -190]

lightSources = ["405 nm", "488 nm", "532 nm", "561 nm", "405/6", "470/9", "528/15"]
lightSourcesNominalPower = [120, 100, 100, 150, 1250, 525, 260]
acquisitionRepeats = 1
acquisitionPositionSetting = ["current", "bookmarked"]
acquisitionPositionSetting_selected = 0
acquisitionChannels = list()
liveChannels = list()
bookmarks = list()
bookmark_consider_same_position_distance_lim = 2 # um
bookmarkBackupPath = "C:/Users/mgflast/Desktop/cryoscope_data/lastSessionBookmarks.bookmarks"
bookmarks_changed = False

### Devices and connections:
camera = "pco.edge 4.2"
cameraConnected = False
lightsource = "LightHUB"
lightsourceConnected = False
controller = "Triggerbox"
controllerConnected = False
cryoStage = "Linkam Cryostage"
cryoStageConnected = False
asiStage = "ASI Filter + Focus stage"
asiStageConnected = False
# Focus stage stuff
focusStep = 100 # nm
focusStepOptions = ["100 nm", "200 nm", "500 nm", "1 um", "2 um", "5 um", "0.1 mm"]
focusStepOptionsValue = [0.1, 0.2, 0.5, 1, 2, 5, 100]
focusStepOptionCurrent = 3
currentFocusPosition = 0.0
filterCubes = ["rsEGFP2", "RGB Reflection", "RFPs", "Empty"]
filterInfo = [
    "dichroic: FF495-Di03 (Semrock), emission: FF01-550/88 (Semrock) - upd. 221209",
    "dichroic: 51000bs (Chroma) - upd. 221209",
    "dichroic: FF570-Di01 (Semrock), emission: FF01-630/92 (Semrock)",
    "no filters",
                ]
currentFilter = 0
filterStageSpeed = 20.0 # mm / s
filterStageAcceleration = 100 # milliseconds to reach the speed setpoint
CRISPState = False
## Arduino listening
arduinoTimeout = 0.001
changing_focus = False
changing_filter = False
# Cryostage stuff
stageMovementSpeed = 500 # um/s
currentPosition = [0.0, 0.0]
centerMarkerPosition = None
currentCondenserPower = 0
stageNotAtPositionError = 0.1
stageMoving = False
snappingBookmark = False
snappingBookmark_complete = False
### Used in AcquisitionControl.py
mode = "idle" # possible modes: "acquiring", "acquisition paused", "snapping", "searching", "mapping", "idle"
last_image_recording_number = None
roi = [0, 0, 2048, 2048]
currentRoi = 2048
sensorSize = 2048
activeChannels = list()
minimumExposure = 10
# ZStack
zStack_top = 0.0
zStack_bottom = 0.0
zStack_delta_up = 500.0
zStack_delta_down = -500.0
zStack_step = 500
zStack_active = False
zStack_options = ["Set top and bottom", "Relative to current"]
zStack_options_active = 1
zStack_home = None
zStack_positions = list()
zStack_latest_position = 0
zStack_num_slices = 0
zStack_folder = "C:/Users/mgflast/Desktop/cryoscope_data"
# acquisition
acquisitionTitle = datestamp()+"_"
acquisitionPower = [20, 20, 20, 20, 5, 5, 5]
acquisitionTotalToSave = 0
acquisitionTotalToAcquire = 0
acquisitionSavedSoFar = 0
acquisitionAcquiredSoFar = 0
acquisitionImageSaveList = None
acquisitionImageTitleList = None
acquisitionImageChannelList = None
acquisitionCurrentFolder = None
# live
livePower = [5, 10, 10, 5, 2, 2, 2]
live_numChannels = 0
live_latestChannel = 0
live_activeChannels = None
live_activeChannelIndex = 0
live_latestPosition = [0.0, 0.0]
live_settingsChanged = False
live_powerChanged = False
# overall
databuffer = None
metadatabuffer = None
#
fanspeed = 43
fanmode = 1 # 0 = auto, 1 = manual
cameraTemperatures = (0, 0, 0)
# maps
maps_title = "new map"
maps_mode = 1 # 0 - roi, 1 - centered
maps_mode_names = ["set ROI", "centered"]
maps_use_crisp = False
maps_roi_coords = [[-1, -1], [1, -1], [1, 1], [-1, 1]]
maps_center = [0.0, 0.0]
maps_centerMode_width = 1
maps_centerMode_height = 1
maps_current_folder = None
maps_total_images = 0
maps_position_list = list()
maps_image_title_list = list()
maps_image_channel_list = list()
maps_image_overlap = 0.2
maps_image_processed = False
maps_requested_position = [0.0, 0.0]
maps_awaiting_position = False
maps_stage_settle_time = 0.5
maps_fixed_condenser_power = 5
currentMap = None
mapChannels = list()


# main
width = 1920
height = 1080
fullscreen = True
defaultTextureSize = (2048, 2048)
shortcuts = [
    "Stop any acquisition   - esc",
    "Acquire                - A",
    "Snap                   - S",
    "Search                 - spacebar",
    "Pause acquisition      - P",
    "Retract objective lens - Q",
]
# Collapsable headers
header_CryostageInfo = True
header_Focus = True
header_ROI = True
header_ZStack = True
header_log = True
header_macros = True
doubleClickInterval = 0.5  # seconds
# renderer
# new camera & stage calibration values
world_to_stage_scale_fac = 2.0 * 1440.0 / 2048.0
cursor_stage_offset = [0.0, -30.0]
# renderer cntd
screenView_zoom = 1.0

screenView_base_zoom = 0.72
screenView_xRange = [318, 1549]
screenView_yRange = [321, 1060]
screenView_xCenter = 0
screenView_yCenter = 0
screenView_base_xOffset = 53
screenView_base_yOffset = -300
cameraOffsetX = 53
cameraOffsetY = -300
cameraZoom = 1.0
cameraZoomSpeed = 0.5
quadOffsetX = 0
quadOffsetY = 0
screenView_translation_ndcPerPixel = 1
screenView_flipHorizontal = False
screenView_flipVertical = False
# renderer / user input
screenView_translate_speed = 2  # turns out to align when this value is 2. easy!
screenView_zoom_speed_smooth = 0.02
screenView_zoom_speed_discrete = 0.24
screenView_zoom_smoothStop_decayrate = 0.07
# GUI_Modules
defaultSpacing = 10
acquisitionNotes_width = 300
acquisitionNotes_height = 100
saveConfigButton_width = 85
saveConfigButton_height = 20
clearConfigButton_width = 45
mainButtons_width = 92
mainButtons_height = 60
progressBar_width = 301
progressBar_size = (8, 293, 8 + progressBar_width, 297)
progressBar_true_color = ()
roiButtons_width = 80
roiButtons_height = 30
roiButtons_separation = 5
roiButtons_top_row_offset = 30
roiButtons_bot_row_offset = 70
autofocusButtonWidth = 92
autofocusButtonHeight = 33
macroButtonWidth = 180
macroButtonHeight = 33
condenserPowerInputOffset = 30
condenserPowerInputWidth = 110
acquisitionChannel_notes_height = 89
addChannelButtonSize = 50
addChannelButtonColumnSize = 100
channelWindowTotalWidth = 1670
bottomPanel_firstColumnWidth = 250
channelCheckbox_size = 20
channelHeader_separator_major = 10
channelHeader_separator_minor = 8
channelLightSource_separator = 8
channelButton_small_size = 20
channel_column_width = 295
source_checkbox_spacing = 70
channelTitleWidth_repeater = 80
channelTitleWidth = 196
channelAddButtonVerticalSpacingCount = 24
laserPowerSlider_offset = 0
histogram_downsample = 10
histogram_range_allowed_max = [200.0, 500.0, 1000.0, 2000.0, 5000.0, 10000.0, 25000.0, 65535.0]
default_config_save_folder = "C:/"
channel_column_width_repeater = 95
channel_column_height = 400
channel_vertical_offset_repeater = 17
repeater_enableCheckbox_offset = 35
repeaterText_horizontal_offset = 14
repeater_right_button_spacing = 35
makeRepeaterButton_width = 110
acquisitionTitle_width = 200
view_histogram_width = 300
view_histogram_height = 60
histogram_num_bins = 100
bookmark_importance_colors = [[0.8, 0.8, 0.8], [74/255.0, 185/255.0, 251/255.0], [1.0, 100/255.0, 100/255.0], [242/255.0, 184/255.0, 47/255.0], [14 / 255.0, 158 / 255.0, 33 / 255.0]]
bookmark_importance_descriptors = ["default", "misc.", "maybe", "good", "center marker"]
bookmark_column_width = 286
bookmark_column_height = 400
bookmark_title_width = 150
bookmark_rating_width = 80
bookmark_goto_button_width = 50
bookmark_goto_button_height = 20
viewChannels = list()
latestAcquisitionMode = "searching"
addBookmark_button_width = 200
addBookmark_button_height = 40

restoreBookmarks_button_height = 20
bookmark_image_width = 200
bookmark_image_height = 200
view_headerButton_height = 40
view_headerButton_width = 145
view_headerButton_hoffset = 0
# 21 12 01
maps_firstColumnWidth = 250
maps_startButton_offset = 50
maps_startButton_width = 140
maps_startButton_height = 50
maps_copyButton_height = 30
maps_coordinatePreviewColumnWidth = 230
maps_setCenter_button_offset = 50
maps_setCenter_button_width = 120
maps_setCenter_button_height = 30
maps_setWidthHeight_width = 90

# 21 11 30 stage stuff
updateInterval = 3  # get temperatures at this interval
updateIntervalCtr = 0.0
updateStagePosInterval = 0.5  # get xy and focus positions at this interval
updateStagePosIntervalCounter = 0.0

# 22 02 19
focusStepButton_width = 100
zStackInputInt_width = 106
zStackSetZButton_width = 40
zStackSetZButton_height = 20
zStackInputFloat_width = 60
zStackInputFloat_position = 70
zStackCombo_width = 190

contextMenuPos = [0.0, 0.0]
contextMenuSize = [150, 60]
contextMenu = False
contextMenuCanClose = False
# general colors
clr_disabled = [0.4, 0.4, 0.4]
clr_disable_grayscale = 0.4
sliderBackgroundColor = [0.09, 0.09, 0.09]  # user for laser power settings
clr_active_mode = (68 / 255.0, 0.85, 47 / 255.0)
clr_imgui_background_default = (14/255.0, 14/255.0, 14/255.0)
clr_warning = (180 / 255, 0.125, 0.007)
clr_text_default = (1.0, 1.0, 1.0)
clr_condenser_on = (0.8, 0.8, 0.4)
clr_emphasis_button = (23 / 255, 115 / 255, 64 / 255)
clr_emphasis_button_hovered = (83 / 255, 175 / 255, 109 / 255)
clr_emphasis_button_2 = (62 / 255, 119 / 255, 189 / 255)
clr_window_titles = (0.0, 0.0, 0.0)
clr_default_imgui_dark_blue = (29 / 255, 46 / 255, 92 / 255)

# logging
log_path = "cryoscope_log"
log_file = None
log_lines = list()
log_level_options = ["Error/warning", "Debug", "Info", "Trace"]
write_log_file = False
log_level = 3
log_lines_shown = 40
logWindowWidth = 300
logWindowHeight = 200

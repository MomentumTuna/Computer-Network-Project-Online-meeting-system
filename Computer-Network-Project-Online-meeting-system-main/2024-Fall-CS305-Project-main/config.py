HELP = 'Create         : create an conference\n' \
       'Join [conf_id ]: join a conference with conference ID\n' \
       'Quit           : quit an on-going conference\n' \
       'Cancel         : cancel your on-going conference (only the manager)\n\n'

SERVER_IP = '127.0.0.1'
MAIN_SERVER_PORT = 8888
TIMEOUT_SERVER = 5
# DGRAM_SIZE = 1500  # UDP
LOG_INTERVAL = 2

AUDIO_CHUNK = 4096
CHANNELS = 1  # Channels for audio capture
RATE = 8000  # Sampling rate for audio capture

camera_width, camera_height = 480, 480  # resolution for camera capture

CONFERENCE1_VIDEO_ADDRESS = (f'{SERVER_IP}',21113)
CONFERENCE1_AUDIO_ADDRESS = (f'{SERVER_IP}',21114)
CONFERENCE2_VIDEO_ADDRESS = (f'{SERVER_IP}',21115)
CONFERENCE2_AUDIO_ADDRESS = (f'{SERVER_IP}',21116)
CONFERENCE3_VIDEO_ADDRESS = (f'{SERVER_IP}',21117)
CONFERENCE3_AUDIO_ADDRESS = (f'{SERVER_IP}',21118)

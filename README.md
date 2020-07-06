# TURING-CAMERA-TIMELAPSE

Service for recording timelapse photo files from camera feed

Service logs output and error messages are stored in:
- /var/lib/turing/turing-camera-timelapse/outputs/out.log
- /var/lib/turing/turing-camera-timelapse/outputs/err.log

## Install requirements

- Requires numpy:
  - On osx:
      pip install numpy
  - On rpi:
      sudo apt-get install python-numpy

- Requires ffmeg:
  - On osx:
      brew install ffmpeg
  - On rpi:
      sudo apt-get update
      sudo apt-get install ffmpeg

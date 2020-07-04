import base64
import calendar
from io import StringIO
from datetime import datetime, timedelta
import errno
import io
import json
import os
import signal
import threading
import time

import imageio
from PIL import Image
import paho.mqtt.client as mqtt

# try:
#     from picamera import PiCamera
# except Exception:
#     pass


class CoreService(object):
    _kill_now = False

    _comm_client = None
    _comm_delay = 0
    _thread_comms = None
    _thread_lock = None

    # _camera = None
    _op_timer = 0

    _system_channel = '/system'
    _data_channel = '/camera/frames'
    _dir_app_data = '/var/lib/turing/turing-camera-timelapse'
    _subdir_photos = 'photos'
    _subdir_movies = 'movies'


    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        #
        # try:
        #     self._camera = PiCamera()
        # except Exception:
        #     self._camera = None

    def start(self):
        self._ensure_directory_structure()

        self._comm_client = mqtt.Client(
            client_id="service_camera_timelapse",
            clean_session=True
        )

        self._comm_client.on_message = self._on_message
        self._comm_client.on_connect = self._on_connect
        self._comm_client.on_publish = self._on_publish
        self._comm_client.on_subscribe = self._on_subscribe

        self._thread_lock = threading.RLock()

        self._thread_comms = threading.Thread(target=self._start_thread_comms)
        self._thread_comms.setDaemon(True)
        self._thread_comms.start()

        while True:
            if self._op_timer >= 60:
                self._ensure_summary_movies()
                self._op_timer = 0

            else:
                self._op_timer += 1

            time.sleep(0.1)

            if self._kill_now:
                break

    def _on_connect(self, client, userdata, flags, rc):
        self._comm_client.subscribe(self._data_channel)

        self.output('{"sender": "service_camera_timelapse", "message": "Connected to GrandCentral."}')

    def _on_message(self, client, userdata, msg):
        msg_struct = None

        if msg.topic == self._data_channel:
            self._ensure_directory_structure()

            now = datetime.utcnow()
            unixtime = calendar.timegm(now.utctimetuple())
            ts = unixtime - (now.second)

            current_year = str(now.year)
            path_photos_year = os.path.join(self._dir_app_data, self._subdir_photos, current_year)
            self._ensure_directory_existence(path_photos_year)

            current_month = str(now.month)
            path_photos_month = os.path.join(self._dir_app_data, self._subdir_photos, current_year, current_month)
            self._ensure_directory_existence(path_photos_month)

            current_day = str(now.day)
            path_photos_day = os.path.join(self._dir_app_data, self._subdir_photos, current_year, current_month, current_day)
            self._ensure_directory_existence(path_photos_day)

            current_hour = str(now.hour+1)
            path_photos_hour = os.path.join(self._dir_app_data, self._subdir_photos, current_year, current_month, current_day, current_hour)
            self._ensure_directory_existence(path_photos_hour)

            try:
                image_base64 = msg.payload

                # ts = time.time()
                # filename = '%s.png' % str(ts)
                filename = os.path.join(path_photos_hour, '%s.jpg'%str(ts))

                if not os.path.exists(filename):
                    fh = open(filename, 'wb')
                    fh.write(base64.b64decode(image_base64))

            except Exception as e:
                print('[CAMERA-TIMELAPSE] problem receiving message: %s' % e)

    def _on_publish(self, mosq, obj, mid):
        pass

    def _on_subscribe(self, mosq, obj, mid, granted_qos):
        self.output('{"sender": "service_camera_timelapse", "message": "Successfully subscribed to GrandCentral /system channel."}')

    def _on_log(self, mosq, obj, level, string):
        pass

    def _connect_to_comms(self):
        print('Connecting to comms system..')

        try:
            self._comm_client.connect(
                'localhost',
                # '10.0.1.34',
                1883,
                60
            )

        except Exception as e:
            print('Could not connect to local GranCentral. Retry in one second.')

            time.sleep(1)
            self._connect_to_comms()

    def _start_thread_comms(self):
        print('Comms thread started.')

        self._thread_lock.acquire()

        try:
            self._connect_to_comms()

        finally:
            self._thread_lock.release()

        print('Connected to comms server.')

        while True:
            self._thread_lock.acquire()

            try:
                if self._comm_delay > 2000:
                    self._comm_client.loop()
                    self._comm_delay = 0

                else:
                    self._comm_delay += 1

            finally:
                self._thread_lock.release()

    def _ensure_directory_structure(self):
        self._ensure_directory_existence(self._dir_app_data)

        path_photos = os.path.join(self._dir_app_data, self._subdir_photos)
        self._ensure_directory_existence(path_photos)

        path_movies = os.path.join(self._dir_app_data, self._subdir_movies)
        self._ensure_directory_existence(path_movies)

    def _ensure_directory_existence(self, dir_path):
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path)

            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise


    def _ensure_summary_movies(self):
        now = datetime.utcnow()

        prior_hour = now - timedelta(hours=1)

        summary_year = prior_hour.year
        summary_month = prior_hour.month
        summary_day = prior_hour.day

        # Increment hour by one since our file storage is 1-indexed

        summary_hour = prior_hour.hour + 1

        self._compile_summary_movie(summary_year, summary_month, summary_day, summary_hour)

    def _compile_summary_movie(self, summary_year, summary_month, summary_day, summary_hour):
        # photo_dir = './frames/'
        # summary_year = 2018
        # summary_month = 6
        # summary_day = 2
        # summary_hour = 24

        # summary_day = 3
        # summary_hour = 2

        photo_dir = '/var/lib/turing/turing-camera-timelapse/photos/%s/%s/%s/%s' % (summary_year, summary_month, summary_day, summary_hour)
        movies_dir = '/var/lib/turing/turing-camera-timelapse/movies'
        export_filetype = 'mp4'

        movie_path = os.path.join(movies_dir, '%s-%s-%s-%s.mp4' % (summary_year, summary_month, summary_day, summary_hour))

        if not os.path.exists(movie_path):
            images = []

            for subdir, dirs, files in os.walk(photo_dir):
                for file in sorted(files):
                    file_path = os.path.join(subdir, file)

                    if file_path.endswith('.jpg'):
                        if not file_path.endswith('.DS_Store'):
                            images.append(imageio.imread(file_path))

            if len(images) > 0:
                try:
                    imageio.mimsave(movie_path, images, format=export_filetype)
                except Exception as e:
                    print('Error: %s' % e)




    # STANDARD SERVICE OPERATION METHODS

    def output(self, msg, channel=_system_channel):
        if self._comm_client:
            self._comm_client.publish(channel, msg)

    def stop(self):
        pass

    def exit_gracefully(self,signum, frame):
        self._kill_now = True

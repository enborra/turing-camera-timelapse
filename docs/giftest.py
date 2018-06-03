# Requires imageio - pip install imageio
# Requires numpy - pip install numpy


import os
import imageio

# photo_dir = './frames/'
summary_year = 2018
summary_month = 6
# summary_day = 2
# summary_hour = 24

summary_day = 3
summary_hour = 2

photo_dir = '/var/lib/turing/turing-camera-timelapse/photos/%s/%s/%s/%s' % (summary_year, summary_month, summary_day, summary_hour)
movies_dir = '/var/lib/turing/turing-camera-timelapse/movies'
export_filetype = 'mp4'

images = []

for subdir, dirs, files in os.walk(photo_dir):
    for file in sorted(files):
        file_path = os.path.join(subdir, file)

        if file_path.endswith('.jpg'):
            if not file_path.endswith('.DS_Store'):
                images.append(imageio.imread(file_path))
                print('loaded an image: %s' % file_path)

try:
    imageio.mimsave(os.path.join(movies_dir, '%s-%s-%s-%s.mp4' % (summary_year, summary_month, summary_day, summary_hour)), images, format=export_filetype)
except Exception,e:
    print('Error: %s' % e)

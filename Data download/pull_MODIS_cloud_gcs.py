import ee
import time
import pandas as pd

ee.Initialize()

def export_oneimage(img,folder,name,scale,crs):
  full_file_name = folder + '_' + name
  task = ee.batch.Export.image.toCloudStorage(img, full_file_name,\
          bucket='india-crop-yield-raw',\
          fileNamePrefix=full_file_name,\
          scale=scale,\
          crs=crs)
  task.start()
  while task.status()['state'] == 'RUNNING':
    print ('Running...')
    # Perhaps task.cancel() at some point.
    time.sleep(10)
  print ('Done.'), task.status()

locations = pd.read_csv('locations_india.csv',header=None)

# Transforms an Image Collection with 1 band per Image into a single Image with items as bands
# Author: Jamie Vleeshouwer

def appendBand(current, previous):
    # Rename the band
    previous=ee.Image(previous)
    current = current.select([0,1,2,3,4,5,6])
    # Append it to the result (Note: only return current item on first element/iteration)
    accum = ee.Algorithms.If(ee.Algorithms.IsEqual(previous,None), current, previous.addBands(ee.Image(current)))
    # Return the accumulation
    return accum

county_region = ee.FeatureCollection('users/DBLobell/India_districts')

imgcoll = ee.ImageCollection('MODIS/MOD09A1') \
    .filterBounds(ee.Geometry.Rectangle(68, 6,100, 36))\
    .filterDate('2000-1-1','2009-12-31')
img=imgcoll.iterate(appendBand)
img=ee.Image(img)

img_0=ee.Image(ee.Number(-100))
img_16000=ee.Image(ee.Number(16000))

img=img.min(img_16000)
img=img.max(img_0)

for loc1, loc2, lat, lon in locations.values:
    fname = '{}_{}'.format(int(loc1), int(loc2))

    # offset = 0.11
    scale  = 500
    crs='EPSG:4326'

    # filter for a county
    region = county_region.filterMetadata('StateCode', 'equals', int(loc1))
    region = ee.FeatureCollection(region).filterMetadata('DistCode', 'equals', int(loc2))
    region = ee.Feature(region.first())

    while True:
        try:
            export_oneimage(img.clip(region), 'data_image_full', fname, scale, crs)
        except Exception as e:
            print (e)
            print ('retry')
            time.sleep(10)
            continue
        break
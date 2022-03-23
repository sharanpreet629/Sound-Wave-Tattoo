import numpy as np
import wave
from pydub import AudioSegment
from image_match.goldberg import ImageSignature
from pydub.playback import play
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from audio import Audio
from PIL import Image
import boto3
import matplotlib.pyplot as plt
from collections import Counter
import cv2

ACCESS_KEY = 'AKIASLURFW5R7GJPTSNM'
SECRET_KEY = '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'


engine = create_engine('sqlite:///audio.db')
Session = sessionmaker(bind = engine)
session = Session()

def text_detection(path):
    documentName = path
    with open(documentName, 'rb') as document:
        imageBytes = bytearray(document.read())

    client = boto3.client('textract',
                          region_name='us-east-1',
                          aws_access_key_id=ACCESS_KEY,
                          aws_secret_access_key=SECRET_KEY)

    response = client.detect_document_text(Document={'Bytes': imageBytes})
    blocks = response['Blocks']
    #block_counts = Counter(x['BlockType'] for x in blocks)

    all_lines = [l for l in blocks if l['BlockType'] == 'LINE']

    for l in all_lines:
        global Key
        Key = l['Text']
        print(Key)
    return Key




def find_distances(image):
    # gis = ImageSignature()
    # #im_sig = gis.generate_signature(image)
    im_key = text_detection(image)
    print(im_key)
    global all_signatures
    all_signatures = session.query(Audio.key).all()
    global distances
    listy = [signature[0] for signature in all_signatures]
    print(listy)
    if im_key in listy:
        index = listy.index(im_key)
        audio_bytes, nchannels, sampwidth, framerate, nframes, comptype, compname = \
            session.query(Audio.audio_bytes, Audio.nchannels, Audio.sampwidth, \
                          Audio.framerate, Audio.nframes, Audio.comptype, Audio.compname).filter(Audio.id \
                          == index + 1).first()

        tune = wave.open('playback_new.wav', 'wb')  # create new audio file with write mode
        tune.setnchannels(nchannels)  # channels 1 = mono 2 = stereo (two because of two ears)
        tune.setsampwidth(sampwidth)
        tune.setframerate(framerate)  # specify frame rate to get number of frames. you have duration and rate
        tune.setnframes(nframes)
        tune.setcomptype(comptype, compname)
        tune.writeframes(audio_bytes)
        tune.close()
        playback = AudioSegment.from_wav('playback_new.wav')
        return print('Done')
    else:
        return print('Not Found')


    # for signature in all_signatures:
    #     # listy = [int(char) for char in signature[0]]
    #     # key_sig = np.array(listy)
    #     # distance = gis.normalized_distance(key_sig, im_sig)
    #     # compute normalized distance between two points.
    #
    #     distances.append(distance)
    # return distances



# def find_match():
#     value = min(distances) # the shortest distance is the most likely match.
#                            # however, a threshold of 0.4 should be set as value to ensure match
#     index = distances.index(value)
#     audio_bytes, nchannels, sampwidth, framerate, nframes, comptype, compname = \
#     session.query(Audio.audio_bytes, Audio.nchannels, Audio.sampwidth,\
#     Audio.framerate, Audio.nframes, Audio.comptype, Audio.compname).filter(Audio.id \
#     == index+1).first()
#
#     tune = wave.open('playback_new.wav','wb') # create new audio file with write mode
#     tune.setnchannels(nchannels) # channels 1 = mono 2 = stereo (two because of two ears)
#     tune.setsampwidth(sampwidth)
#     tune.setframerate(framerate) # specify frame rate to get number of frames. you have duration and rate
#     tune.setnframes(nframes)
#     tune.setcomptype(comptype, compname)
#     tune.writeframes(audio_bytes)
#     tune.close()
#     playback = AudioSegment.from_wav('playback_new.wav')
#     print('Done')

im = Image.open('IMG-1323.jpg')
im.save('new_check.png')
img = cv2.imread('new_check.png')
imgFloat = img.astype(np.float) / 255.
mgFloat = img.astype(np.float) / 255.
kChannel = 1 - np.max(imgFloat, axis=2)
kChannel = (255 * kChannel).astype(np.uint8)
binaryThresh = 120
_, binaryImage = cv2.threshold(kChannel, binaryThresh, 255, cv2.THRESH_BINARY_INV)

cv2.imwrite("sample.png", binaryImage)



# gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
# x1,x2,y1,y2= 100,1500,100,700
# k=cv2.rectangle(gray, (x1, y1), (x1+x2, y1+y2) ,(255,0, 0), 2)
# cropped = img[x1:x2,y1:y2]
# # dst = cv2.fastNlMeansDenoisingColored(img,None,10,10,20,20)
# cv2.imwrite("sample.png", k)
# #adaptive = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,4)
# #_,thresh = cv2.threshold(new, 20, 255, cv2.THRESH_BINARY)


#find_distances(image= "gray.png")

#find_match()
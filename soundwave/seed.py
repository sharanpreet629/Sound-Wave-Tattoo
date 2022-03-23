import matplotlib.pyplot as plt
import numpy as np
import os
import wave
from pydub import AudioSegment

from image_match.goldberg import ImageSignature
from pydub.playback import play

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from audio import Audio

import boto3
import glob
import os
from collections import Counter

ACCESS_KEY = 'AKIASLURFW5R7GJPTSNM'
SECRET_KEY = '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'

engine = create_engine('sqlite:///audio.db')
Session = sessionmaker(bind = engine)
session = Session()



def read_audio(file_name):
    global fname
    fname = file_name.split('.')[0]
    global audio
    audio = wave.open(file_name,'r')
    return audio, fname

def play_audio(file_name, seconds = 0, first = False, last = False, reverse = False):
    play_ = AudioSegment.from_wav(file_name)
    if reverse == False:
        if seconds == 0:
            return play(play_)
        elif seconds < int(play_.duration_seconds):
            x_seconds = seconds*1000
            if first == True:
                return play(play_[:x_seconds])
            elif first == False:
                return play(play_[:x_seconds])
            elif last == True:
                return play(play_[-x_seconds:])
            elif last == False:
                return play(play_[:x_seconds])
        else:
            return 'Seconds exceeds duration of audio sample'
    else:
        if seconds == 0:
            return play(play_.reverse())
        elif seconds < int(play_.duration_seconds):
            x_seconds = seconds*1000
            if first == True:
                return play(play_[:x_seconds].reverse())
            elif first == False:
                return play(play_[:x_seconds].reverse())
            elif last == True:
                return play(play_[-x_seconds:].reverse())
            elif last == False:
                return play(play_[:x_seconds].reverse())
        else:
            return 'Seconds exceeds duration of audio sample'

def plot_audio(name):
    color = input('Which color do you want to plot(r/g/b): ')
    global signal_byte
    signal_byte = audio.readframes(-1)
    signal = np.fromstring(signal_byte, 'int16')
    freq = audio.getframerate()

    time = np.linspace(0, len(signal)/freq, num=len(signal))

    plt.figure(1, figsize=(10,9))
    plt.plot(time,signal, color)
    plt.axis('off')
    print(name)
    namel = name.split('/')[1:]
    print(namel)
    random_key = namel[0]+namel[2]
    path = f'graphs/{namel[0]}_{namel[1]}_{namel[2]}_key.png'
    plt.savefig(path)
    return path, random_key

def write_text(path, unique_key):
    img = Image.open(path)
    img1 = ImageDraw.Draw(img)
    myFont = ImageFont.truetype('FreeMono.ttf',40)
    img1.text((450,800),unique_key,fill=(125,125,125),font=myFont)
    img.save(path)


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


def image2db(path, key):
    name = fname
    gis = ImageSignature()
    image_key = gis.generate_signature(path)
    image_sig = str(list(image_key))
    audio_b = signal_byte
    parameters = audio.getparams()
    nchannels = parameters[0]
    sampwidth = parameters[1]
    framerate = parameters[2]
    nframes = parameters[3]
    comptype = parameters[4]
    compname = parameters[5]
    instance = Audio(name = name, key = key,  image_signature = image_sig, \
    audio_bytes = audio_b, nchannels = nchannels, sampwidth = sampwidth, \
    framerate = framerate, nframes = nframes, comptype = comptype, compname = compname) # create an audio instance

    session.add(instance) # add to database
    session.commit()

audio_extensions = ['.wav']
audios = [os.path.join(dp, f) for dp, dn, filenames in os.walk('Speak_Recog_Data (copy)') for f in filenames if os.path.splitext(f)[1].lower() in audio_extensions]
print(audios)
for path in audios[4:5]:
    audio, name= read_audio(path)
    #play_audio(file_name)
    path, unique_key= plot_audio(name)
    print(path)
    write_text(path,unique_key)
    key = text_detection(path)
    image2db(path,key)
    print(f'Saved to database audio file: {name}')
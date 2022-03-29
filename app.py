import numpy as np
import os
# import wave
# import cv2
from werkzeug.utils import secure_filename
import matplotlib.pyplot as plt
from flask import Flask, request, render_template, jsonify, send_from_directory, redirect, flash
import wave
import datetime
# from pydub import AudioSegment

# from image_match.goldberg import ImageSignature
# from pydub.playback import play

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from db.db import db
from audio import Audio
from models.app_model import Profile

# import boto3
# import glob


UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) 

app = Flask(__name__, static_url_path="/static")
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
audio_extensions = ['wav']
image_extensions = ['jpeg','png','jpg']


ACCESS_KEY = 'AKIASLURFW5R7GJPTSNM'
SECRET_KEY = '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'


engine = create_engine('sqlite:///Audio.db')
Session = sessionmaker(bind = engine)
session = Session()

db.init_app(app)

#user defined functions
def read_audio(file_name):
	global fname
	fname = file_name.split('.')[0]
	global audio
	audio = wave.open(file_name,'r')
	return audio, fname

def plot_audio(name):
	#color = input('Which color do you want to plot(r/g/b): ')
	global signal_byte
	signal_byte = audio.readframes(-1)
	signal = np.fromstring(signal_byte, 'int16')
	freq = audio.getframerate()

	time = np.linspace(0, len(signal)/freq, num=len(signal))

	plt.figure(1, figsize=(10,9))
	plt.plot(time,signal)
	plt.axis('off')
	print(name)
	namel = name.split('/')[1:]
	random_key = namel[-1]
	path = '/static/{}.png'.format(random_key)
	print(path)
	plt.savefig(path)
	#plt.show()
	name = str(random_key)+'.png'
	return name, path,random_key

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

#find_distances()

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif','wav'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def Home():
	return "Hello World"

@app.route('/uploader', methods=['GET', 'POST'])
def upload_file():
	if request.method == 'POST':
		file = request.files['']
		if file.filename == '':
			resp = jsonify({'message': 'No file selected for uploading'})
			resp.status_code = 400
			return resp
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			try:
				query_path =(os.path.join(app.config['UPLOAD_FOLDER'],filename))
				file.save(query_path)
				return query_path
		
			except Exception as e:
				resp = 'Something went wrong please try again later'
				return resp
 			
			

			if query_path.split('.')[-1] in audio_extensions:
				audio, name = read_audio(query_path)
				n, path, unique_key = plot_audio(name)
				print(path)
				write_text(path, unique_key)
				#key = text_detection(path)
				key = 'sa2'
				#print(key)
				image2db(path, key)
				print(f'Saved to database audio file: {n}')
				resp = jsonify({
				    'msg': 'success',
				    # 'size': [img.width, img.height],
				    # 'format': img.format,
				    'filename': filename
				    # 'img': data
				})
				resp.status_code = 201
				return resp

			elif query_path.split('.')[-1] in image_extensions:
				print('hlo')
				im = Image.open(query_path)
				im.save('new_query.png')
				resp = jsonify({
				    'msg': 'success',
				    # 'size': [img.width, img.height],
				    # 'format': img.format,
				    'filename': 'playback_test.wav'
				    # 'img': data
				})
				resp.status_code = 201
				return resp

	else:
		resp = jsonify({'message': 'Allowed file types are png, jpg, jpeg, wav'})
		resp.status_code = 400
		return resp

download_directory = os.path.join(os.getcwd(), '/static')
@app.route("/uploader/<path:path>", methods= ['GET', 'POST'])
def get_file(path):
	return send_from_directory(download_directory,path, as_attachment=True)

if __name__=='__main__':
	app.run(debug=True)

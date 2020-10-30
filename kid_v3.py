
"""Virtual Assistant - K.I.D. V3
K.I.D stand for Knowledge Integrated device :)

Prerequisites: 
You will have to download K.I.D. android app in your android device to communicate with K.I.D.
To use Home automation mode, You will have to run PI_board.py in Raspberry Pi.
To use Windows application mode & Smart Vision mode, you will have run this code in your windows machine.

Android App provides 3 modes,
A)  Home automation mode: To controls IOT switch board which was programmed using Raspberry Pi, relay also has been used to control AC devices
B)  Windows application mode: To control some of windows applications, Voice typing is also supported
C)  Smart Vision mode: Used for real time visual surveillance purpose, based on command it’ll monitor/alert/detect the object in camera. YOLO had been used for live video detection.

"""

#firebase database
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

#yolo
import cv2
from darkflow.net.build import TFNet

# To use NLP
import nltk
from nltk.stem.lancaster import LancasterStemmer
stemmer = LancasterStemmer()

#Tensorflow
import numpy as np
import tflearn
import tflearn
import tensorflow as tf

import random
import win32com.client as wincl 
import re
import time
from PIL import ImageGrab
from time import sleep
import os
import webbrowser
import wikipedia

#import win32com.client as wincl
speak = wincl.Dispatch("SAPI.SpVoice")

#Extract dataset
#Import our chat-bot intents file
import json
with open('R34_Developing_Dataset_final.json') as json_data:
    intents = json.load(json_data)

"""**Preprocessing for coversation chat bot**"""

#Pre Processing

words = []
classes = []
documents = []
ignore_words = ['?']
# loop through each sentence in our intents patterns
for intent in intents['intents']:
    for pattern in intent['patterns']:
        # tokenize each word in the sentence
        w = nltk.word_tokenize(pattern)
        # add to our words list
        words.extend(w)
        # add to documents in our corpus
        documents.append((w, intent['tag']))
        # add to our classes list
        if intent['tag'] not in classes:
            classes.append(intent['tag'])

# stem and lower each word and remove duplicates
words = [stemmer.stem(w.lower()) for w in words if w not in ignore_words]
words = sorted(list(set(words)))

# remove duplicates
classes = sorted(list(set(classes)))

classes_count =0
for t_x in classes: classes_count=classes_count+1
    
# create our training data
training = []
output = []
# create an empty array for our output
output_empty = [0] * len(classes)

# training set, bag of words for each sentence
for doc in documents:
    # initialize our bag of words
    bag = []
    # list of tokenized words for the pattern
    pattern_words = doc[0]
    # stem each word
    pattern_words = [stemmer.stem(word.lower()) for word in pattern_words]
    # create our bag of words array
    for w in words:
        bag.append(1) if w in pattern_words else bag.append(0)

    # output is a '0' for each tag and '1' for current tag
    output_row = list(output_empty)
    output_row[classes.index(doc[1])] = 1
    #print ("doc[0]: ", doc[0])
    #print ("pattern_words: ", pattern_words)
    #print ("bag: ", bag)
    #print ("output_row: ", output_row)
    training.append([bag, output_row])


# shuffle our features and turn into np.array
random.shuffle(training) 
training = np.array(training)

# create train and test lists
train_x = list(training[:,0])
train_y = list(training[:,1])
train_x_count,train_y_count=0,0 
for t_x in train_x: train_x_count=train_x_count+1
for t_y in train_y: train_y_count=train_y_count+1

# reset underlying graph data
tf.reset_default_graph()

# Build neural network
net = tflearn.input_data(shape=[None, len(train_x[0])])
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, len(train_y[0]), activation='softmax')
net = tflearn.regression(net)

# Define model and setup tensorboard
model = tflearn.DNN(net, tensorboard_dir='tflearn_logs')
# Start training (apply gradient descent algorithm)
model.fit(train_x, train_y, n_epoch=200, batch_size=8, show_metric=True)

#for just try
# create a data structure to hold user context
context = {}
spk= str()

ERROR_THRESHOLD = 0.25                                  
def classify(sentence):
    # generate probabilities from the model
    results = model.predict([bow(sentence, words)])[0]
    # filter out predictions below a threshold
    results = [[i,r] for i,r in enumerate(results) if r>ERROR_THRESHOLD]
    # sort by strength of probability
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append((classes[r[0]], r[1]))
    # return tuple of intent and probability
    return return_list

def response(sentence, userID='123', show_details=False):
    results = classify(sentence)
    #print (results)
    # if we have a classification then find the matching intent tag
    if results:
        # loop as long as there are matches to process
        while results:
            for i in intents['intents']:
                # find a tag matching the first result
                if i['tag'] == results[0][0]:
                    # set context for this intent if necessary
                    if 'context_set' in i:
                        if show_details: print ('context:', i['context_set'])
                        context[userID] = i['context_set']

                    # check if this intent is contextual and applies to this user's conversation
                    if not 'context_filter' in i or \
                        (userID in context and 'context_filter' in i and i['context_filter'] == context[userID]):
                        if show_details: print ('tag:', i['tag'])
                        # a random response from the intent
                        spk=random.choice(i['responses'])
                        return spk,results

            results.pop(0)

def clean_up_sentence(sentence):
    # tokenize the pattern
    sentence_words = nltk.word_tokenize(sentence)
    # stem each word
    sentence_words = [stemmer.stem(word.lower()) for word in sentence_words]
    return sentence_words

# return bag of words array: 0 or 1 for each word in the bag that exists in the sentence
def bow(sentence, words, show_details=False):
    # tokenize the pattern
    sentence_words = clean_up_sentence(sentence)
    # bag of words
    bag = [0]*len(words)  
    for s in sentence_words:
        for i,w in enumerate(words):
            #print(i,w)
            if w == s: 
                bag[i] = 1
                if show_details:
                    print ("found in bag: %s" % w)

    return(np.array(bag))

def firebase_update_desktop():
    flag_s = root.child("desktop/flag").get()
    n_ref_s = root.child('desktop')
    msg_S = root.child("desktop/input").get()
    n_ref_s.update({'input' :""})
    n_ref_s.update({'flag' :""})
    return msg_S

while True:
    ip = str(input('Ask me something: '))
    
    if ip=='close':
        break
    spk,results=response(ip)
    print(results)
    print(spk)
    speak.Speak(spk)

"""### App Version
**After running below you can ask anything by app. You have to choose KID option before asking/speaking any query from app. Speak 'stop' to stop conversation.**
"""

try:
    app = firebase_admin.get_app()
except ValueError as e:
    cred = credentials.Certificate(".\\xyz.json")
    firebase_admin.initialize_app(cred, {"databaseURL": "your firebase link"})
    root = db.reference()

while True:
    flag = root.child("desktop/flag").get()
    if(flag == '1') or (flag == "1"):
        ip=firebase_update_desktop()
        try:
            conf = classify(ip)
            conf = conf[0][1]
        except:
            conf = 1

        ip = str(ip)
        if ip=='stop':
            speak.Speak("Okay, have a good day")
            break
        if (conf<0.5) or (spk==None):
            try:
                text_data_list1 = []
                ip = ip.split(' ')
                msg = ' '.join(ip[2:]) #seprating keyword
                wikipedia.set_lang('en') #bling speech - FREE 5,000 transactions free per month
                speak.Speak("Kindly wait, I am searching for you about it in wikipedia.")
                text_data = wikipedia.summary(msg, sentences=2) #IF KEYWORD DOESNT WORK GIVE CHANCE TO ADD KEYWORD BY TEXT
                text_data = re.sub(r'\(.+?\)\s*', '', text_data)
                text_data_list = text_data.split(".")
                for i in text_data_list:
                    text_data_list1.append(i+'.')
                string_data = text_data_list1[0] + text_data_list1[1]
                print('------------------------------------------------------------------------------')
                print('Brief Review about : '+msg)
                print(string_data)
                speak.Speak(string_data)
            except Exception as e:
                speak.Speak("There is no such answer is wikipedia so let me redirect you to google")
                url='http://google.com/search?q='+str(ip)
                speak.Speak("opening web browser")
                webbrowser.open(url)
                speak.Speak('Google Results for: '+str(ip))
        else:        
            spk,results=response(ip)
            print(results)
            print(spk)
            speak.Speak(spk)

print("No of classes:",classes_count)
print("No of training set:",train_x_count)

speak = wincl.Dispatch("SAPI.SpVoice")
try:
    app = firebase_admin.get0._app()
except ValueError as e:
    cred = credentials.Certificate(".\\xyz.json")
    firebase_admin.initialize_app(cred, {"databaseURL": "your firebase link"})
    root = db.reference()

def firebase_update_SmartVision():
    flag_s = root.child("smart_vision/flag").get()
    n_ref_s = root.child('smart_vision')
    msg_S = root.child("smart_vision/input").get()
    n_ref_s.update({'input' :""})
    n_ref_s.update({'flag' :""})
    return msg_S

msg = firebase_update_SmartVision()

def object(msg):
    text_data_list1 = []
    msg = msg.split(' ')
    msg = ' '.join(msg[3:])
    return msg #seprating keyword

i_object=object(msg)
#i_object='person'

options={
    'model':'cfg/yolo.cfg', #path of the model
    'load':'bin/yolov2.weights', #path of the weights
    'threshold': 0.2,   #it is how much or how good a confidence factor it needs to have in order to draw the bounding box
                        # if it's too low then no of boxes will be more there
}

tfnet = TFNet(options)
colors = [tuple(255 * np.random.rand(3)) for _ in range(10)] #creates rgb values for 10 different colors


capture = cv2.VideoCapture(0)
capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
flag=0

while True:
    ret, frame = capture.read()

    if ret: #if capture device is recording...
        results = tfnet.return_predict(frame) #continuously takes the frames and stores pred in results

        for color, result in zip(colors, results):
            #retriving all the parameters
            tl = (result['topleft']['x'], result['topleft']['y'])
            br = (result['bottomright']['x'], result['bottomright']['y'])
            label = result['label']
            confidence = result['confidence']

            if i_object==label:
            #to draw rectangle with the classified label
                text = '{}: {:.0f}%'.format(label, confidence * 100)
                frame = cv2.rectangle(frame, tl, br, color, 3)
                frame = cv2.putText(frame, text, tl, cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 2)
                flag=1
                #os.system('espeak("Alert. object identified.")')
                speak.Speak('Alert. Alert. object identified'+'Yes, I can see '+i_object)

                cv2.imshow('frame', frame)
                sleep(0.10)
                snapshot = ImageGrab.grab()
                save_path = "D:\\KID\\Yolo\\darkflow-master\\detected_image\\img.jpg"
                snapshot.save(save_path)
                break

        cv2.imshow('frame', frame)


        #print('FPS {:.1f}'.format(1 / (time.time() - stime)))
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

if flag==0:
    print("object not found")
    #replace with speech
else:
    print('object identified')
    #replace with speech
capture.release()
cv2.destroyAllWindows()

"""# Thank you :)"""
































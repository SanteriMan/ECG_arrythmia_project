# -*- coding: utf-8 -*-
"""ECG_arrhytmia_project.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1YbUaUno4CMuUmABR9ZqdVW-3XRQJde2V

Instruction
For the analysis, you should:
1. Use pre-processing techniques (such as filtering) if necessary.
2. Detect R-peaks of each ECG record
3. Extract features from the shape of the heart cycles: e,g., amplitude and duration of QRS
complex, duration of the ST segment, T-wave duration (see ecg features).
4. Divide your dataset into the training set and test set (70-30% split).
5. Standardize your data: i.e., use the mean and standard deviation of the training data to
standardize the training data and the test data.
6. Select two supervised machine learning algorithms and train two classifiers using the train
set. Each classifier should predict 1 in the presence of arrhythmia or 0 otherwise.
7. Compare the two classifiers by evaluating the results using the test set.
a. Obtain the confusion matrix, accuracy, precision, recall, and F1-score. These can be
calculated from the predicted and true values.

Santeri Mäntyniemi sjjman@utu.fi <br>
Jan Böhmeke jebohm@utu.fi

# Importing libraries

Installing biosppy package for QRS detection
"""

!pip install biosppy

"""Importing required libraries"""

# Commented out IPython magic to ensure Python compatibility.
# Libraries
from sklearn.decomposition import PCA

# Library for loading the data as a data frame and for the first task
import pandas as pd

# Library for plotting the histograms and boxplots
import matplotlib.pyplot as plt

# Library for plotting the scatter plots and heatmaps
import seaborn as sns

# For normalization
from sklearn import preprocessing

# Show the plots inline in the notebook
# %matplotlib inline

import os

import numpy as np

from glob import glob

from sklearn.model_selection import train_test_split

from tqdm import tqdm   #show loop progress meter

import glob

from biosppy.signals import ecg

from scipy import stats

from scipy import signal

from sklearn.utils import shuffle

from sklearn.neighbors import KNeighborsClassifier

from sklearn import metrics

from sklearn.decomposition import PCA

"""Importing data from google drive

"""

from google.colab import drive
drive.mount('/content/drive')
#!ls "/content/drive/My Drive"

"""# Data visualization"""

abnormal_sample =  pd.read_csv("/content/drive/My Drive/Biosignal Analytics 2021/Data/abnormal/sample_ID100_0.csv")
normal_sample = pd.read_csv("/content/drive/My Drive/Biosignal Analytics 2021/Data/normal/sample_ID100_0.csv")

plt.figure(figsize=(12,7))
plt.plot(abnormal_sample, label='abnormal', color="red")
plt.plot(normal_sample, label='normal')
plt.show()

"""# Initial parameters"""

normal_sample = np.array(normal_sample["Lead II"])
abnormal_sample = np.array(abnormal_sample["Lead II"])

fs = len(normal_sample)/10 #Sampling rate, number of samples/sampling time
sample_size = 10 #seconds
path = "/content/drive/My Drive/Biosignal Analytics 2021/Data/"
class_list = ["normal/","abnormal/"]

"""Plotting a sample"""

mySample = pd.read_csv(path + class_list[0] + "sample_ID100_0.csv")
ts = np.arange(0,10,1/fs)
fig = plt.figure(figsize=(12,7))
plt.plot(ts, mySample)
plt.ylabel("Amplitude")
plt.xlabel("Time (second)")
plt.show()

"""# Set filenames and labels"""

filenames = []
labels = []

for idx, cl in enumerate(class_list):
    files_list = glob.glob(path + cl + "/*.csv")
    filenames.extend(files_list)
    labels.extend([idx]*len(files_list))

len(filenames) #7901 files with 3855 labeled as normal ECG and 4046 labeled as abnormal ECG

"""# Filtering example"""

plt.figure(figsize=(12, 7))
plt.plot(ts, mySample["Lead II"])
plt.title("Normal ECG sample",fontsize=16)
plt.xlabel("Time (seconds)",fontsize=16)
plt.ylabel("Amplitude",fontsize=16)
plt.show()

fc = np.array([0.5,40])
Wn = fc/(fs/2)
b, a = signal.butter(4, Wn, btype ='bandpass', analog=False)

filtered_sample = signal.filtfilt(b, a, mySample["Lead II"])
plt.figure(figsize=(12, 7))
plt.plot(ts, filtered_sample)
plt.title("Butterworth filtered sample",fontsize=16)
plt.xlabel("Time (seconds)",fontsize=16)
plt.ylabel("Amplitude",fontsize=16)
plt.show()

"""# R-peak detection example"""

ECG_peaks = ecg.hamilton_segmenter(filtered_sample, sampling_rate = fs)
plt.figure(figsize=(12, 7))
plt.plot(filtered_sample)
plt.plot(ECG_peaks[0], filtered_sample[ECG_peaks], "x")
plt.xlabel("Samples",fontsize=16)
plt.ylabel("Amplitude",fontsize=16)
plt.title("ECG normal with peak detection",fontsize=16)
plt.show()

"""#R-peak detection and feature extraction for all signals"""

#Extracting waveform
def extract_waveform(arr, locs):
  w1,w2= int(0.4*fs), int(0.6*fs)
  waveforms = []
  for loc in locs:
    if (loc - w1 > 0) and (loc + w2 < len(arr)):
      l1, l2 = loc - w1, loc + w2
      waveforms.append(arr[l1:l2])
  return waveforms

#Example with ensemble average waveform
#First detecting R-peaks of a signal
R_peaks = ecg.hamilton_segmenter(signal = filtered_sample, sampling_rate =360)

#Splitting the signal into waveforms and calculating the average waveform
waveforms_ecg = extract_waveform(filtered_sample, R_peaks[0])
avg_waveform_ecg = np.mean(np.array(waveforms_ecg), axis=0)

plt.figure(figsize=(12, 7))
for waveform in waveforms_ecg:
  plt.plot(waveform)
plt.plot(avg_waveform_ecg, linewidth = 3, color = 'k')
plt.title("Example of ECG Ensemble Average Waveform")
plt.xlabel("Samples",fontsize=16)
plt.ylabel("Amplitude",fontsize=16)
plt.show()

feature_matrix = pd.DataFrame(columns=["avg_waveform","r_loc","r_amplitude","rr_interval","t_loc","s_loc","st_duration","q_loc","qrs_duration","p_loc","pr_interval"])
for idx, fn in tqdm(enumerate(filenames)):
  
    #import a file
    df = pd.read_csv(fn)
    
    #filter the signals
    fc = np.array([0.5,40])
    Wn = fc/(fs/2)
    b, a = signal.butter(4, Wn, btype ='bandpass', analog=False)

    filtered = np.array(signal.filtfilt(b, a, df["Lead II"]))

    #Finding the R-peaks
    ECG_peaks = ecg.hamilton_segmenter(filtered, sampling_rate = fs)

    #R-R interval in seconds
    peak_times_s = ECG_peaks[0] / fs
    RR_intervals = np.diff(peak_times_s) 
    avg_RR_interval = np.average(RR_intervals)

    #Creating ensemble average waveform
    waveforms_ecg = extract_waveform(filtered, ECG_peaks[0])
    avg_waveform_ecg = np.mean(np.array(waveforms_ecg), axis=0)

    #R-peak location
    r_loc = np.argmax(avg_waveform_ecg)
    
    #R-peak amplitude
    r_amplitude = avg_waveform_ecg[r_loc]

    #T-wave peak location
    start = int(0.6*fs)
    end = int(0.8*fs)
    t_loc = start + np.argmax(avg_waveform_ecg[start:end])

    #Q-wave peak location
    q_loc = 128 + np.argmin(avg_waveform_ecg[128:144])

    #S-wave peak location
    s_loc =  144 + np.argmin(avg_waveform_ecg[144:160])
    
    #ST-duration in seconds
    st_duration = (t_loc - s_loc) / fs

    #QRS-duration in seconds
    qrs_duration = (s_loc - q_loc) / fs

    #P-wave peak location
    p_loc = 50 + np.argmax(avg_waveform_ecg[50:120])
   
    #PR-interval in seconds 
    pr_interval = (r_loc - p_loc) / fs

    feature_matrix.loc[idx] = avg_waveform_ecg, r_loc, r_amplitude, avg_RR_interval, t_loc, s_loc, st_duration, q_loc, qrs_duration, p_loc, pr_interval

feature_matrix

#change this to plot other signals
filenum = 250

plt.figure(figsize=(12, 7))
plt.plot(feature_matrix["avg_waveform"][filenum])
plt.plot(feature_matrix["r_loc"][filenum], feature_matrix["avg_waveform"][filenum][feature_matrix["r_loc"][filenum]], 'ro')
plt.plot(feature_matrix["t_loc"][filenum], feature_matrix["avg_waveform"][filenum][feature_matrix["t_loc"][filenum]], 'ko')
plt.plot(feature_matrix["s_loc"][filenum], feature_matrix["avg_waveform"][filenum][feature_matrix["s_loc"][filenum]], 'bo')
plt.plot(feature_matrix["p_loc"][filenum], feature_matrix["avg_waveform"][filenum][feature_matrix["p_loc"][filenum]], 'go')
plt.plot(feature_matrix["q_loc"][filenum], feature_matrix["avg_waveform"][filenum][feature_matrix["q_loc"][filenum]], 'mo')
plt.title("ECG average ensemble waveform with QRS, P and T locations")
plt.show()
print(labels[filenum])
print(filenames[filenum])

"""Moreover, Training Data extracts 5 features in the temporal domain [36] for each ECG cycle. The
features include QRS complex duration, T wave duration, RR interval, PR interval and ST segment. -- HiCH: Hierarchical Fog-Assisted Computing Architecture
for Healthcare IoT

# kNN Classifier
"""

#QRS-amplitude, QRS-duration, RR-interval, PR-interval and ST-duration as features
X = feature_matrix[["r_amplitude","rr_interval","st_duration","qrs_duration","pr_interval"]].copy()
#Labels: 0 for normal, 1 for abnormal
y = np.array(labels)

#Splitting into 70% training set/30% testing set
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=1)

#Normalizing data
X_train_mean = np.mean(X_train, axis=0)
X_train_std = np.std(X_train, axis=0)
X_train_norm = (X_train - X_train_mean)/X_train_std
X_test_norm = (X_test - X_train_mean)/X_train_std

clf = KNeighborsClassifier(n_neighbors=3)

clf.fit(X_train_norm, y_train)

y_pred = clf.predict(X_test_norm)
confusion_matrix = metrics.confusion_matrix(y_test, y_pred)

print("Confusion matrix:")
print(metrics.confusion_matrix(y_test, y_pred))
print("Precision: {:.3f}".format(metrics.precision_score(y_test, y_pred)))
#print(metrics.precision_score(y_test, y_pred, average=None))
print("Recall: {:.3f}".format(metrics.recall_score(y_test, y_pred)))
#print(metrics.recall_score(y_test, y_pred, average=None))
print("F1 score: {:.3f}".format(metrics.f1_score(y_test, y_pred)))
#print(metrics.f1_score(y_test, y_pred, average=None))
print("Accuracy: {:.3f}".format(metrics.accuracy_score(y_test,y_pred)))

"""# SVM Classifier"""

from sklearn.svm import SVC

clf = SVC()

clf.fit(X_train_norm, y_train)

y_pred = clf.predict(X_test_norm)
confusion_matrix = metrics.confusion_matrix(y_test, y_pred)

print("Confusion matrix:")
print(metrics.confusion_matrix(y_test, y_pred))
print("Precision: {:.3f}".format(metrics.precision_score(y_test, y_pred)))
#print(metrics.precision_score(y_test, y_pred, average=None))
print("Recall: {:.3f}".format(metrics.recall_score(y_test, y_pred)))
#print(metrics.recall_score(y_test, y_pred, average=None))
print("F1 score: {:.3f}".format(metrics.f1_score(y_test, y_pred)))
#print(metrics.f1_score(y_test, y_pred, average=None))
print("Accuracy: {:.3f}".format(metrics.accuracy_score(y_test,y_pred)))

"""# Principal Component Analysis"""

#Computing PCA with two components
pca = PCA(n_components=2)
pca_out = pca.fit_transform(X)

cdict = {0:'blue',1:'red'}

#Plotting with first component as x-axis and second component as y-axis
plt.figure(figsize=(10,10))
for i in range(len(X)):
  plt.scatter(pca_out[:,0][i],pca_out[:,1][i], c=cdict[y[i]])


plt.xlabel('PC1',fontsize=16)
plt.ylabel('PC2',fontsize=16)

plt.show()

###########################################################################################################################################################################################
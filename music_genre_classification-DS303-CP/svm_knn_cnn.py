# -*- coding: utf-8 -*-
"""svm_knn_cnn.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1k7HrZHgSV9z87w8ZXvkoVYjo6UPY8GyP
"""

import numpy as np

def loadall(filename=''):
    tmp = np.load(filename)
    x_tr = tmp['x_tr']
    y_tr = tmp['y_tr']
    x_te = tmp['x_te']
    y_te = tmp['y_te']
    x_cv = tmp['x_cv']
    y_cv = tmp['y_cv']
    return {'x_tr' : x_tr, 'y_tr' : y_tr,
            'x_te' : x_te, 'y_te' : y_te,
            'x_cv' : x_cv, 'y_cv' : y_cv, }

import numpy as np
import tensorflow as tf
import keras
from keras import backend as K
from keras.models import Sequential, load_model
from keras.layers import Dense, Dropout, Flatten
from keras.layers import Conv2D, MaxPooling2D
from keras.layers import BatchNormalization
from keras.utils import np_utils
from keras import regularizers
from keras.engine.topology import Layer
from sklearn.metrics import precision_recall_fscore_support, confusion_matrix

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
import itertools


def plot_confusion_matrix(cm, classes,
                          normalize=False,
                          title='Confusion matrix',
                          cmap=plt.cm.Blues):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        print("Normalized confusion matrix")
    else:
        print('Confusion matrix, without normalization')

    print(cm)

    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)

    fmt = '.1f' if normalize else 'd'
    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j], fmt),
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")

    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.tight_layout()


# Models to be passed to Music_Genre_CNN

song_labels = ["Blues","Classical","Country","Disco","Hip hop","Jazz","Metal","Pop","Reggae","Rock"]


def metric(y_true, y_pred):
    return K.mean(K.equal(K.argmax(y_true, axis=1), K.argmax(y_pred, axis=1)))

def cnn(num_genres=10, input_shape=(64,173,1)):
    model = Sequential()
    model.add(Conv2D(64, kernel_size=(4, 4),
                     activation='relu', #kernel_regularizer=regularizers.l2(0.04),
                     input_shape=input_shape))
    model.add(BatchNormalization())
    model.add(MaxPooling2D(pool_size=(2, 4)))
    model.add(Conv2D(64, (3, 5), activation='relu'
                    , kernel_regularizer=regularizers.l2(0.04)
                    ))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.2))
    model.add(Conv2D(64, (2, 2), activation='relu'
       # , kernel_regularizer=regularizers.l2(0.04)
        ))
    model.add(BatchNormalization())
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.2))
    model.add(Flatten())
    model.add(Dense(64, activation='relu', kernel_regularizer=regularizers.l2(0.04)))
    model.add(Dropout(0.5))
    model.add(Dense(32, activation='relu', kernel_regularizer=regularizers.l2(0.04)))
    model.add(Dense(num_genres, activation='softmax'))
    model.compile(loss=keras.losses.categorical_crossentropy,
                  optimizer=keras.optimizers.Adam(lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=1e-08, decay=0.0),
                  metrics=[metric])
    return(model)


# Main network thingy to train

class model(object):

    def __init__(self, ann_model):
        self.model = ann_model()

    def train_model(self, train_x, train_y,
                val_x=None, val_y=None,
                small_batch_size=110, max_iteration=300, print_interval=1,
                test_x=None, test_y=None):

        m = len(train_x)

        for it in range(max_iteration):

            # split training data into even batches
            batch_idx = np.random.permutation(m)
            train_x = train_x[batch_idx]
            train_y = train_y[batch_idx]

            num_batches = int(m / small_batch_size)
            for batch in range(num_batches):

                x_batch = train_x[ batch*small_batch_size : (batch+1)*small_batch_size]
                y_batch = train_y[ batch*small_batch_size : (batch+1)*small_batch_size]
                print("starting batch\t", batch, "\t Epoch:\t", it)
                self.model.train_on_batch(x_batch, y_batch)

            if it % print_interval == 0:
                validation_accuracy = self.model.evaluate(val_x, val_y)
                training_accuracy = self.model.evaluate(train_x, train_y)
                testing_accuracy = self.model.evaluate(test_x, test_y)
                # print of test error used only after development of the model
                print("\nTraining accuracy: %f\t Validation accuracy: %f\t Testing Accuracy: %f" %
                      (training_accuracy[1], validation_accuracy[1], testing_accuracy[1]))
                print("\nTraining loss: %f    \t Validation loss: %f    \t Testing Loss: %f \n" %
                      (training_accuracy[0], validation_accuracy[0], testing_accuracy[0]))
                print( )

            if (validation_accuracy[1] > .81):
                print("Saving confusion data...")
                model_name = "model" + str(100*validation_accuracy[1]) + str(100*testing_accuracy[1]) + ".h5"
                self.model.save(model_name) 
                pred = self.model.predict_classes(test_x, verbose=1)
                cnf_matrix = confusion_matrix(np.argmax(test_y, axis=1), pred)
                np.set_printoptions(precision=2)
                plt.figure()
                plot_confusion_matrix(cnf_matrix, classes=song_labels, normalize=True, title='Normalized confusion matrix')
                print(precision_recall_fscore_support(np.argmax(test_y, axis=1),pred, average='macro')) 
                plt.savefig(str(batch))


def main():

# Data stuff

    data = loadall('/content/drive/MyDrive/DS303-Music Genre Classification Course Project/melspects.npz')

    x_tr = data['x_tr']
    y_tr = data['y_tr']
    x_te = data['x_te']
    y_te = data['y_te']
    x_cv = data['x_cv']
    y_cv = data['y_cv']

    tr_idx = np.random.permutation(len(x_tr))
    te_idx = np.random.permutation(len(x_te))
    cv_idx = np.random.permutation(len(x_cv))

    x_tr = x_tr[tr_idx]
    y_tr = y_tr[tr_idx]
    x_te = x_te[te_idx]
    y_te = y_te[te_idx]
    x_cv = x_cv[cv_idx]
    y_cv = y_cv[cv_idx]

    x_tr = x_tr[:,:,:,np.newaxis]
    x_te = x_te[:,:,:,np.newaxis]
    x_cv = x_cv[:,:,:,np.newaxis]

    y_tr = np_utils.to_categorical(y_tr)
    y_te = np_utils.to_categorical(y_te)
    y_cv = np_utils.to_categorical(y_cv)
    ann = model(cnn)
    ann.train_model(x_tr, y_tr, val_x=x_cv, val_y=y_cv, test_x=x_te, test_y=y_te)

if __name__ == '__main__':
    main()

x = cnn()

x.summary()

"""cnn model

Training accuracy: 0.932250	 

Validation accuracy: 0.843750	 

Testing Accuracy: 0.828125

Training loss: 0.848888    	 Validation loss: 1.312548    	 Testing Loss: 1.233908

SVM
"""

import numpy as np
from sklearn import svm
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA


data = loadall('/content/drive/MyDrive/DS303-Music Genre Classification Course Project/melspects.npz')
x_tr = data['x_tr']
y_tr = data['y_tr']
x_te = data['x_te']
y_te = data['y_te']
x_cv = data['x_cv']
y_cv = data['y_cv']

print('shape of training data', x_tr.shape)

x_tr = x_tr.reshape(x_tr.shape[0], x_tr.shape[1]*x_tr.shape[2])
x_cv = x_cv.reshape(x_cv.shape[0], x_cv.shape[1]*x_cv.shape[2])
x_te = x_te.reshape(x_te.shape[0], x_te.shape[1]*x_te.shape[2])

scaler = StandardScaler()
# Fit on training set only.
scaler.fit(x_tr)
# Apply transform to both the training set and the test set.
train_sc = scaler.transform(x_tr)
cv_sc = scaler.transform(x_cv)
test_sc = scaler.transform(x_te)

pca = PCA(n_components = 15)
pca.fit(train_sc)

train_pca = pca.transform(train_sc)
cv_pca = pca.transform(cv_sc)
test_pca = pca.transform(test_sc)

print(pca.n_components_)

classifier = svm.SVC(gamma='scale', verbose=True)
classifier.fit(train_pca, y_tr)



train_preds = classifier.predict(train_pca)
train_acc = np.sum(train_preds == y_tr)
train_acc = train_acc / len(y_tr)

cv_preds = classifier.predict(cv_pca)
cv_acc = np.sum(cv_preds == y_cv)
cv_acc = cv_acc / len(y_cv)

test_preds = classifier.predict(test_pca)
test_acc = np.sum(test_preds == y_te)
test_acc = test_acc / len(y_te)

print('Train: ', train_acc, "\tCV: ", cv_acc, "\tTest: ", test_acc)

"""KNN"""

import numpy as np
import random
import math
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.neighbors import KNeighborsClassifier


PCA_TOGGLE = True

data = loadall('/content/drive/MyDrive/DS303-Music Genre Classification Course Project/melspects.npz')
x_tr = data['x_tr']
y_tr = data['y_tr']
x_te = data['x_te']
y_te = data['y_te']
x_cv = data['x_cv']
y_cv = data['y_cv']

print('here1', x_tr.shape)
# print(y_cv)

x_tr = x_tr.reshape(x_tr.shape[0], x_tr.shape[1]*x_tr.shape[2])
x_cv = x_cv.reshape(x_cv.shape[0], x_cv.shape[1]*x_cv.shape[2])
x_te = x_te.reshape(x_te.shape[0], x_te.shape[1]*x_te.shape[2])

scaler = StandardScaler()
# Fit on training set only.
scaler.fit(x_tr)
# Apply transform to both the training set and the test set.
train_sc = scaler.transform(x_tr)
cv_sc = scaler.transform(x_cv)
test_sc = scaler.transform(x_te)

print('here2')

if PCA_TOGGLE == True:
	pca = PCA(n_components = 15)
	pca.fit(train_sc)

	train_pca = pca.transform(train_sc)
	cv_pca = pca.transform(cv_sc)
	test_pca = pca.transform(test_sc)

	print(pca.n_components_)

	neigh = KNeighborsClassifier(n_neighbors=5, weights='distance')
	neigh.fit(train_pca, y_tr)

	train_preds = neigh.predict(train_pca)
	train_acc = np.sum(train_preds == y_tr)
	train_acc = train_acc / len(y_tr)

	cv_preds = neigh.predict(cv_pca)
	cv_acc = np.sum(cv_preds == y_cv)
	cv_acc = cv_acc / len(y_cv)

	test_preds = neigh.predict(test_pca)
	test_acc = np.sum(test_preds == y_te)
	test_acc = test_acc / len(y_te)

	print('Train: ', train_acc, "\tCV: ", cv_acc, "\tTest: ", test_acc)
	# print(preds)

else:
	neigh2 = KNeighborsClassifier(n_neighbors=10, weights='distance')
	neigh2.fit(train_sc, y_tr)

	preds = neigh2.predict(cv_sc)
	acc = np.sum(preds == y_cv)
	acc = acc / len(y_cv)
	print('Accuracy is {}'.format(acc))
	print(preds)

"""KNN without PCA"""

import numpy as np
import random
import math
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.neighbors import KNeighborsClassifier


PCA_TOGGLE = False

data = loadall('/content/drive/MyDrive/DS303-Music Genre Classification Course Project/melspects.npz')
x_tr = data['x_tr']
y_tr = data['y_tr']
x_te = data['x_te']
y_te = data['y_te']
x_cv = data['x_cv']
y_cv = data['y_cv']

print('here1', x_tr.shape)
# print(y_cv)

x_tr = x_tr.reshape(x_tr.shape[0], x_tr.shape[1]*x_tr.shape[2])
x_cv = x_cv.reshape(x_cv.shape[0], x_cv.shape[1]*x_cv.shape[2])
x_te = x_te.reshape(x_te.shape[0], x_te.shape[1]*x_te.shape[2])

scaler = StandardScaler()
# Fit on training set only.
scaler.fit(x_tr)
# Apply transform to both the training set and the test set.
train_sc = scaler.transform(x_tr)
cv_sc = scaler.transform(x_cv)
test_sc = scaler.transform(x_te)

print('here2')

if PCA_TOGGLE == True:
	pca = PCA(n_components = 15)
	pca.fit(train_sc)

	train_pca = pca.transform(train_sc)
	cv_pca = pca.transform(cv_sc)
	test_pca = pca.transform(test_sc)

	print(pca.n_components_)

	neigh = KNeighborsClassifier(n_neighbors=5, weights='distance')
	neigh.fit(train_pca, y_tr)

	train_preds = neigh.predict(train_pca)
	train_acc = np.sum(train_preds == y_tr)
	train_acc = train_acc / len(y_tr)

	cv_preds = neigh.predict(cv_pca)
	cv_acc = np.sum(cv_preds == y_cv)
	cv_acc = cv_acc / len(y_cv)

	test_preds = neigh.predict(test_pca)
	test_acc = np.sum(test_preds == y_te)
	test_acc = test_acc / len(y_te)

	print('Train: ', train_acc, "\tCV: ", cv_acc, "\tTest: ", test_acc)
	# print(preds)

else:
	neigh2 = KNeighborsClassifier(n_neighbors=10, weights='distance')
	neigh2.fit(train_sc, y_tr)

	preds = neigh2.predict(cv_sc)
	acc = np.sum(preds == y_cv)
	acc = acc / len(y_cv)
	print('Accuracy is {}'.format(acc))
	print(preds)
 

  test_preds = neigh2.predict(test_pca)
  test_acc = np.sum(test_preds == y_te)
  test_acc = test_acc / len(y_te)

  print('Train: ', train_acc, "\tCV: ", cv_acc, "\tTest: ", test_acc)
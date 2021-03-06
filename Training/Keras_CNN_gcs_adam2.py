from __future__ import print_function
import keras
from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten
from keras.layers import Conv2D, MaxPooling2D
from keras.layers.normalization import BatchNormalization
from keras import backend as K
import matplotlib
matplotlib.use("agg")
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import sklearn
from sklearn import metrics

## Loading the cleaned images downloaded from the MODIS Satellite for 4 counties in 2003. This is to inspect the
## dimensions of the cleaned images.

## We then convert our images to histogram buckets so that each X image has dimensions 32*32*9 (32 buckets, 9 bands, 32 timesteps)
## Loading and inspecting the dimensions of the histogram npz files

image_hist = np.load('./data_output_full_histogram_all_full_2.npz')

X_all = image_hist["output_image"]
Y_all = image_hist["output_yield"]

s = np.arange(X_all.shape[0])
np.random.shuffle(s)

X_shuffled = X_all[s]
Y_shuffled = Y_all[s]

X_train = X_all[0:1200, :, :, :]
Y_train = Y_all[0:1200].reshape(1200, 1)

X_val = X_all[1200:1338, :, :, :]
Y_val = Y_all[1200:1338].reshape(138, 1)

X_test = X_all[1339:1477, :, :, :]
Y_test = Y_all[1339:1477].reshape(138, 1)

# Checking shape of x_train and y_train
print(X_train.shape)
print(Y_train.shape)

print(X_val.shape)
print(Y_val.shape)

print(X_test.shape)
print(Y_test.shape)


def error_metric(y_true, y_pred):
    return K.sqrt(K.mean(K.square(y_pred - y_true), axis=-1))


def squared_error(ys_orig, ys_line):
    return sum((ys_line - ys_orig) * (ys_line - ys_orig))


def coefficient_of_determination(ys_orig, ys_line):
    y_mean_line = [np.mean(ys_orig) for y in ys_orig]
    squared_error_regr = squared_error(ys_orig, ys_line)
    squared_error_y_mean = squared_error(ys_orig, y_mean_line)
    return (1 - (squared_error_regr / squared_error_y_mean))


batch_size = 20
epochs = 200
img_rows, img_cols, channels = 32, 32, 9  # input image dimensions

input_shape = (img_rows, img_cols, channels)

# print('X_train shape:', X_train.shape)
# print(X_train.shape[0], 'train samples')
# print(X_test.shape[0], 'test samples')

# no of filters maybe reduced
'''
model = Sequential()
model.add(Conv2D(128, kernel_size=(3, 3), activation='relu', padding='same', input_shape=input_shape))
model.add(Conv2D(128, kernel_size=(3, 3), strides = 2, activation='relu', padding='same'))
model.add(Dropout(0.5))
model.add(Conv2D(256, kernel_size=(3, 3), strides = 1, activation='relu', padding='same'))
model.add(Dropout(0.5))
model.add(Conv2D(256, kernel_size=(3, 3), strides = 2, activation='relu', padding='same'))
model.add(Dropout(0.5))
model.add(Conv2D(512, kernel_size=(3, 3), strides = 1, activation='relu', padding='same'))
model.add(Dropout(0.5))
model.add(Conv2D(512, kernel_size=(3, 3), strides = 1, activation='relu', padding='same'))
model.add(Dropout(0.5))
model.add(Conv2D(1024, kernel_size=(3, 3), strides = 1, activation='relu', padding='same'))
# model.add(BatchNormalization())
model.add(Flatten())
model.add(Dense(2048, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(1))'''

model = Sequential()
model.add(Conv2D(128, kernel_size=(3, 3), activation='relu', padding='same', input_shape=input_shape))
model.add(Conv2D(256, kernel_size=(3, 3), activation='relu', padding='same'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Conv2D(512, kernel_size=(3, 3), strides = 1, activation='relu', padding='same'))
model.add(Dropout(0.2))
model.add(Conv2D(512, kernel_size=(3, 3), strides = 1, activation='relu', padding='same'))
model.add(Dropout(0.2))
#model.add(BatchNormalization())
model.add(Flatten())
model.add(Dense(512, activation='relu'))
model.add(Dropout(0.3))
model.add(Dense(1))


#opt_adadelta = keras.optimizers.Adadelta(lr=1.0, rho=0.95, epsilon=None, decay=0.0)
opt_adam = keras.optimizers.Adam(lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0.005, amsgrad=False)

model.compile(loss=keras.losses.mean_squared_error, optimizer = opt_adam, metrics=[error_metric, 'mape'])

history = model.fit(X_train, Y_train, batch_size=batch_size, epochs=epochs, verbose=1, shuffle=True, validation_data=(X_val, Y_val))

f = open('output_Adam1.txt','w')

## Running on validation data
y_pred_train = model.predict(X_train)
r2error = coefficient_of_determination(Y_train, y_pred_train)
print('R2 error for train set:', r2error[0], file=f)

## train data
score_val = model.evaluate(X_train, Y_train, verbose=1)
print('Loss on training', score_val[0], file=f)
print('RMSE on training', score_val[1], file=f)
print('MAPE on training:', score_val[2], file=f)

## validation data
score_val = model.evaluate(X_val, Y_val, verbose=1)
print('Loss on validation', score_val[0], file=f)
print('RMSE on dev', score_val[1], file=f)
print('MAPE on dev:', score_val[2], file=f)

## test data
#score_test = model.evaluate(X_test, Y_test, verbose=1)
#print('Loss on test', score_test[0], file=f)
#print('RMSE on test:', score_test[1], file=f)
#print('MAPE on test:', score_test[2], file=f)


## Running on validation data

y_pred_val = model.predict(X_val)

xval = list(range(138))

pp = PdfPages('output_images_Adam2.pdf')

plt.figure(0)
plt.plot(xval, Y_val, 'r--',label="Y actual")
plt.plot(xval, y_pred_val, 'b--',label="Y predicted")
plt.legend(loc ="upper left")
plt.xlabel("Epoch")
plt.ylabel("Yield")
plt.title("Predicted vs Actual Yield for Validation Set")
pp.savefig()
plt.savefig('YpredvsYactual_Simpler_Adam2.png')
#fig1.show()

plt.figure(1)
plt.plot(history.history['val_mean_absolute_percentage_error'])
plt.xlabel("Epoch")
plt.ylabel("MAPE")
plt.title("MAPE for validation set")
# plt.ylim( 0, 300 )
pp.savefig()

plt.savefig('MAPE_simpler_Adam2.png')

plt.figure(2)
plt.plot(history.history['val_error_metric'])

plt.xlabel("Epoch")
plt.ylabel("RMSE")
plt.title("RMSE for validation set")
pp.savefig()
plt.savefig('RMSE_simpler_Adam2.png')
#plt.ylim(0,2)


plt.figure(3)
plt.plot(history.history['loss'])

plt.xlabel("Epoch")
plt.ylabel("Loss (MSE)")
plt.title("Loss for training")
pp.savefig()
plt.savefig('Loss_history_training_Adam2.png')


## Running on test data

#y_pred_test = model.predict(X_test)

#print(history.history.keys())
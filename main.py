'''
@author: Imildo Sitoe <imildo.sitoe@iu-study.org>
@description: this file contains the main calls to the classes and methods of other related files and is the file responsible for starting the entire program. 
'''

from sqlalchemy.orm import sessionmaker
import database as db
import data_loading as dl
import numpy as np
import pandas as pd
import warnings
import unittest
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt


#Creating a session
Session = sessionmaker(bind=db.engine)
session = Session()

# Calling a function to ignore a future warning during scattering of the last chart
warnings.simplefilter(action='ignore', category=FutureWarning)

# Creating the database and its tables
db.createAllTables()

# Calling the statement to load Training and Ideal data into the database, but birst verify whether the csv data have been already loaded into the db
if pd.DataFrame(session.query(db.Train.__table__).all()).shape[0] == 0:
    dl.DataLoading.loadChangesDB()

# Querying Train data from sqlite database and converting to dataframe
train_data = session.query(db.Train.__table__).all()
df_train = pd.DataFrame(train_data)
x_train = df_train[['x']]
y_train = df_train.drop(columns=['id', 'x'])

# Querying Ideal data from sqlite database and converting to dataframe
ideal_data = session.query(db.Ideal.__table__).all()
df_ideal = pd.DataFrame(ideal_data)
x_ideal = df_ideal[['x']]
y_ideal = df_ideal.drop(columns=['id', 'x'])

# Querying Test data from sqlite database and converting to dataframe
test_data = session.query(db.Test.__table__).all()
df_test = pd.DataFrame(test_data)
x_test = df_test[['x']]
y_test = df_test[['y']]

# Ploting and visualizing the original data logically as described in the task
plt.scatter(x_train, y_train[['y1']], color='red')
plt.scatter(x_train, y_train[['y2']], color='green')
plt.scatter(x_train, y_train[['y3']], color='magenta')
plt.scatter(x_train, y_train[['y4']], color='blue')
plt.xlabel('X value')
plt.ylabel('Y value')
plt.title('ORIGINAL DATA')
plt.show()

# Section responsible for training, predicting, and testing the model as well as creating its visualization.
# Creating a linear regression model and training it
lr = LinearRegression()
lr.fit(x_train, y_train)

# Executing the prediction of x and visualizing logically
y_pred_train = lr.predict(x_train)
plt.scatter(y_train, y_pred_train)
plt.xlabel('Y training')
plt.ylabel('Y prediction training')
plt.title('PREDICTION DATA')
plt.show()

# Testing the model using the test dataset
y_pred_test = lr.predict(x_test)

# Deviation and Ideal functions section (Choosing the ideal function)
# Calculating and returning the sum of squared y deviations for each ideal function for the provided training data
def sum_squared_dev(y_train, y_ideal):
    return np.sum((y_train - y_ideal) ** 2, axis=0)

# Summing the squared deviations by calling the function sum_squared_dev
ideal_function_errors = sum_squared_dev(y_train, y_ideal)

# Choosing the 4 ideal functions that minimize the sum of squared deviations
chosen_ideal_indices = np.argsort(ideal_function_errors)[:4]
chosen_ideal_functions = y_ideal.iloc[:, chosen_ideal_indices]

# Deviation and Ideal functions section (mapping and calculating the deviation)
# Deviation calculation for x-y pair and ideal function
def get_deviation(y_test, y_ideal):
    return np.sqrt(np.sum((y_test - y_ideal) ** 2))

# Attribute x-y pairs from the test dataset to the chosen ideal functions
deviations = []
assignments = []

for i in range(len(x_test)):
    y_val = y_test.iloc[[i]]
    assigned_function = None
    min_dev = float('inf')

    for j, ideal_function in enumerate(chosen_ideal_functions.T):
        if j == 4:
            break
        else:
            deviation = get_deviation(y_val, ideal_function).item()
            ife = pd.DataFrame(ideal_function_errors)
            df = pd.DataFrame(chosen_ideal_indices)
            cii = df[0].iloc[j]

            if deviation < min_dev and deviation >= np.sqrt(2) * np.max(ife[0].iloc[cii]):
                min_dev = deviation
                assigned_function = j
            
    if assigned_function is not None:
        assignments.append(assigned_function)
        deviations.append(min_dev)
    else:
        assignments.append(None)
        deviations.append(None)

# Saving the deviations and the nr of ideal functions into the SQLite db
if df_test['delta_y'].iloc[1] == 0 or df_test['delta_y'].iloc[1] == None:
    dl.DataLoading.loadDeviations(assignments, deviations)

# Logically visualize the chosen ideal functions
# Plot the chosen ideal functions
for i, ideal_function in enumerate(chosen_ideal_functions.T):
    plt.plot(x_ideal.iloc[i], ideal_function)

# Plot the test data with assignments and deviations
for i, assignment in enumerate(assignments):
    if assignment is not None:
        color = ['b', 'g', 'r', 'm'][assignment]
        plt.scatter(float(x_test.iloc[i]), float(y_test.iloc[i]), marker='.', color=color)

plt.xlabel('X')
plt.ylabel('Y')
plt.title('IDEAL FUNCTIONS AND DEVIATIONS VISUALIZATION')
plt.show()

# Class for unit tests for the program
class TestDevCalculation(unittest.TestCase):
    def test_dev_calculation(self):
        y_test = np.array([1.0, 2.0, 3.0])
        y_ideal = np.array([0.5, 2.5, 3.5])
        deviation = get_deviation(y_test, y_ideal)
        self.assertAlmostEqual(deviation, 0.5, delta=1e-6)
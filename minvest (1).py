# -*- coding: utf-8 -*-
"""minvest.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/11QkqvmpFLpAqII5EndDqGapeKv5IXO_y

Project Overview:

This project includes multiple models to predict a stock's price and analyze potential investment opportunities:
1. **Linear Models (Ridge, Lasso, ElasticNet)**: Regularization techniques used to prevent overfitting, optimized with RandomizedSearchCV.
    - Optimised regression methods such as ridge or lasso used over linear regression for better performance through a better cost function.
2. **Ensemble Models (Random Forest, Gradient Boosting, CatBoost)**: Capture non-linear relationships and interactions, use early stopping for regularization.
    - **CatBoost**: Unique model but used as it handles categorical data natively, requires less hyperparameter tuning, and is efficient with high performance on large datasets.
3. **LSTM**: Recurrent neural network for time series forecasting, incorporates dropout and early stopping.
4. **Monte Carlo Simulation**: Provides probabilistic future stock price ranges, including mean, median, and confidence intervals.
5. **Ichimoku Cloud**: Technical indicator for trend analysis, visualizes support and resistance levels.
6. **NLP on 10-K Statements**: Sentiment analysis using VADER on 10-K filings of Dow Jones companies.
7. **ResNet (CNN)**: Deep convolutional neural network known for handling complex patterns. Pre-trained ResNet50 model is fine-tuned for predicting stock prices.
8. **RNN**: Recurrent neural network suitable for time series data, capturing temporal dependencies.
9. **Quantum CNN**: Combines quantum computing principles with classical CNN, leveraging quantum circuits to enhance data processing. Experimental and assumes access to quantum computing resources.

Optimizations include regularization, hyperparameter tuning, feature engineering, and advanced visualizations. The results help in predicting stock prices, understanding market trends, and making informed investment decisions.
This code uses AAPL for stock predictions and all Dow Jones stocks for the sentiment analysis. If you wish to run the predictions on any other stock, simply change the ticker in the code.
"""

!pip install yfinance pandas numpy matplotlib tensorflow nltk sec-edgar-downloader catboost ta pennylane

import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from catboost import CatBoostRegressor
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler, PolynomialFeatures, MinMaxScaler
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import LSTM, Dense, Dropout, GlobalAveragePooling2D, SimpleRNN, Conv2D, MaxPooling2D, Flatten, Input
from tensorflow.keras.applications import ResNet50
import pennylane as qml
from pennylane.operation import Observable
from pennylane.qnn import KerasLayer
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import os
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from scipy.stats import uniform
import ta
import cv2

# Fetch data from Yahoo Finance
start_date = "2016-01-01"
end_date = datetime.now().strftime('%Y-%m-%d')
df = yf.download('AAPL', start=start_date, end=end_date)

# Feature Engineering
df['MA10'] = df['Adj Close'].rolling(window=10).mean()
df['MA20'] = df['Adj Close'].rolling(window=20).mean()
df['MA50'] = df['Adj Close'].rolling(window=50).mean()
df['EMA10'] = df['Adj Close'].ewm(span=10, adjust=False).mean()
df['EMA20'] = df['Adj Close'].ewm(span=20, adjust=False).mean()
df['EMA50'] = df['Adj Close'].ewm(span=50, adjust=False).mean()
df['RSI'] = ta.momentum.rsi(df['Adj Close'], window=14)
df['MACD'] = ta.trend.macd_diff(df['Adj Close'])
df['High_Low_Diff'] = df['High'] - df['Low']
df['Open_Close_Diff'] = df['Open'] - df['Close']

# Create lagged features
for lag in range(1, 6):
    df[f'Lag_{lag}'] = df['Adj Close'].shift(lag)

# Drop NaN values
df = df.dropna()

# Prepare the data
features = ['MA10', 'MA20', 'MA50', 'EMA10', 'EMA20', 'EMA50', 'RSI', 'MACD', 'High_Low_Diff', 'Open_Close_Diff'] + [f'Lag_{lag}' for lag in range(1, 6)]
X = df[features]
y = df['Adj Close']

# Create interaction terms
poly = PolynomialFeatures(degree=2, include_bias=False, interaction_only=True)
X_interactions = poly.fit_transform(X)

# Feature Scaling
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_interactions)

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, shuffle=False)

### Linear Regression Models ###

# Ridge Regression with RandomizedSearchCV
ridge = Ridge()
ridge_params = {'alpha': uniform(0.1, 100)}
ridge_search = RandomizedSearchCV(ridge, ridge_params, n_iter=20, cv=5, random_state=42)
ridge_search.fit(X_train, y_train)
ridge_best = ridge_search.best_estimator_

# Lasso Regression with RandomizedSearchCV
lasso = Lasso(max_iter=5000)
lasso_params = {'alpha': uniform(0.1, 100)}
lasso_search = RandomizedSearchCV(lasso, lasso_params, n_iter=20, cv=5, random_state=42)
lasso_search.fit(X_train, y_train)
lasso_best = lasso_search.best_estimator_

# ElasticNet with RandomizedSearchCV
elasticnet = ElasticNet(max_iter=5000)
elasticnet_params = {'alpha': uniform(0.1, 100), 'l1_ratio': uniform(0.1, 0.9)}
elasticnet_search = RandomizedSearchCV(elasticnet, elasticnet_params, n_iter=20, cv=5, random_state=42)
elasticnet_search.fit(X_train, y_train)
elasticnet_best = elasticnet_search.best_estimator_

# Predictions on test set
ridge_test_predictions = ridge_best.predict(X_test)
lasso_test_predictions = lasso_best.predict(X_test)
elasticnet_test_predictions = elasticnet_best.predict(X_test)

# Evaluate Linear Models
ridge_test_rmse = np.sqrt(mean_squared_error(y_test, ridge_test_predictions))
lasso_test_rmse = np.sqrt(mean_squared_error(y_test, lasso_test_predictions))
elasticnet_test_rmse = np.sqrt(mean_squared_error(y_test, elasticnet_test_predictions))

print(f'Ridge Test RMSE: {ridge_test_rmse}')
print(f'Lasso Test RMSE: {lasso_test_rmse}')
print(f'ElasticNet Test RMSE: {elasticnet_test_rmse}')

# Plot Linear Regression Predictions
plt.figure(figsize=(14,7))
plt.plot(df.index[-len(y_test):], y_test, label='Actual Prices')
plt.plot(df.index[-len(y_test):], ridge_test_predictions, label='Ridge Predicted Prices')
plt.plot(df.index[-len(y_test):], lasso_test_predictions, label='Lasso Predicted Prices')
plt.plot(df.index[-len(y_test):], elasticnet_test_predictions, label='ElasticNet Predicted Prices')
plt.legend()
plt.title('Linear Regression Models Predictions')
plt.show()

### Tree-based Models ###

# Random Forest with RandomizedSearchCV
rf = RandomForestRegressor()
rf_params = {'n_estimators': [50, 100], 'max_features': ['sqrt'], 'max_depth': [5, 10]}
rf_search = RandomizedSearchCV(rf, rf_params, n_iter=20, cv=5, random_state=42)
rf_search.fit(X_train, y_train)
rf_best = rf_search.best_estimator_

# Gradient Boosting with RandomizedSearchCV and early stopping
gbr = GradientBoostingRegressor()
gbr_params = {'n_estimators': [100, 200], 'learning_rate': uniform(0.01, 0.1), 'max_depth': [3, 5]}
gbr_search = RandomizedSearchCV(gbr, gbr_params, n_iter=20, cv=5, random_state=42)
gbr_search.fit(X_train, y_train)
gbr_best = gbr_search.best_estimator_

# CatBoost with RandomizedSearchCV and early stopping
catboost = CatBoostRegressor(verbose=0)
catboost_params = {'iterations': [500, 1000], 'learning_rate': uniform(0.01, 0.1), 'depth': [4, 6], 'early_stopping_rounds': [50]}
catboost_search = RandomizedSearchCV(catboost, catboost_params, n_iter=20, cv=5, random_state=42)
catboost_search.fit(X_train, y_train, eval_set=(X_test, y_test))
catboost_best = catboost_search.best_estimator_

# Predictions on test set
rf_test_predictions = rf_best.predict(X_test)
gbr_test_predictions = gbr_best.predict(X_test)
catboost_test_predictions = catboost_best.predict(X_test)

# Evaluate Tree-based Models
rf_test_rmse = np.sqrt(mean_squared_error(y_test, rf_test_predictions))
gbr_test_rmse = np.sqrt(mean_squared_error(y_test, gbr_test_predictions))
catboost_test_rmse = np.sqrt(mean_squared_error(y_test, catboost_test_predictions))

print(f'Random Forest Test RMSE: {rf_test_rmse}')
print(f'Gradient Boosting Test RMSE: {gbr_test_rmse}')
print(f'CatBoost Test RMSE: {catboost_test_rmse}')

### LSTM Model ###

# Prepare data for LSTM
scaler = MinMaxScaler()
scaled_data = scaler.fit_transform(df[['Adj Close', 'RSI', 'MACD', 'High_Low_Diff', 'Open_Close_Diff']])
sequence_length = 60
X, y = [], []

for i in range(sequence_length, len(scaled_data)):
    X.append(scaled_data[i-sequence_length:i])
    y.append(scaled_data[i, 0])

X, y = np.array(X), np.array(y)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

# LSTM Model
model = Sequential()
model.add(LSTM(units=50, return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2])))
model.add(Dropout(0.2))
model.add(LSTM(units=50, return_sequences=False))
model.add(Dropout(0.2))
model.add(Dense(units=25))
model.add(Dense(units=1))

model.compile(optimizer='adam', loss='mean_squared_error')

# Early stopping
early_stopping = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

# Train the model
model.fit(X_train, y_train, batch_size=32, epochs=100, validation_data=(X_test, y_test), callbacks=[early_stopping])

# Predictions on test set
test_predict = model.predict(X_test)
test_predict = scaler.inverse_transform(np.concatenate((test_predict, np.zeros((test_predict.shape[0], 4))), axis=1))[:,0]

# Evaluate LSTM Model
lstm_test_rmse = np.sqrt(mean_squared_error(y_test, test_predict))
print(f'LSTM Test RMSE: {lstm_test_rmse}')

# Plot LSTM predictions
plt.figure(figsize=(14,7))
plt.plot(df.index[-len(y_test):], df['Adj Close'].iloc[-len(y_test):], label='Actual Prices')
plt.plot(df.index[-len(y_test):], test_predict, label='LSTM Predicted Prices')
plt.legend()
plt.show()

### CNN Model ###

# Preprocess data for CNN
def preprocess_data(df, sequence_length=60):
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(df[['Adj Close']])

    X, y = [], []
    for i in range(sequence_length, len(scaled_data)):
        X.append(scaled_data[i-sequence_length:i])
        y.append(scaled_data[i, 0])

    X, y = np.array(X), np.array(y)

    # Resize to 32x32 to meet ResNet input requirements
    X_resized = np.zeros((X.shape[0], 32, 32, 3))
    for i in range(X.shape[0]):
        resized_image = cv2.resize(X[i], (32, 32))
        X_resized[i] = np.stack([resized_image]*3, axis=-1)

    return X_resized, y

X, y = preprocess_data(df)

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

# Load ResNet50 model with pre-trained weights
base_model = ResNet50(weights='imagenet', include_top=False, input_shape=(32, 32, 3))

# Add custom layers on top of ResNet
x = base_model.output
x = GlobalAveragePooling2D()(x)
x = Dense(1024, activation='relu')(x)
predictions = Dense(1)(x)

# Define the model
model = Model(inputs=base_model.input, outputs=predictions)

# Compile the model
model.compile(optimizer='adam', loss='mean_squared_error')

# Train the model
model.fit(X_train, y_train, epochs=10, batch_size=32, validation_data=(X_test, y_test))

# Predictions
test_predict = model.predict(X_test)

# Evaluate
test_rmse = np.sqrt(mean_squared_error(y_test, test_predict))
print(f'ResNet Test RMSE: {test_rmse}')

# Plot predictions
plt.figure(figsize=(14, 7))
plt.plot(df.index[-len(y_test):], df['Adj Close'].iloc[-len(y_test):], label='Actual Prices')
plt.plot(df.index[-len(y_test):], test_predict, label='ResNet Predicted Prices')
plt.legend()
plt.show()

### RNN Model ###

# Prepare data for RNN
def preprocess_data_rnn(df, sequence_length=60):
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(df[['Adj Close']])

    X, y = [], []
    for i in range(sequence_length, len(scaled_data)):
        X.append(scaled_data[i-sequence_length:i])
        y.append(scaled_data[i, 0])

    X, y = np.array(X), np.array(y)
    return X, y

X, y = preprocess_data_rnn(df)

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

# Define the RNN model
model = Sequential()
model.add(SimpleRNN(50, return_sequences=True, input_shape=(X_train.shape[1], 1)))
model.add(Dropout(0.2))
model.add(SimpleRNN(50))
model.add(Dropout(0.2))
model.add(Dense(25))
model.add(Dense(1))

# Compile the model
model.compile(optimizer='adam', loss='mean_squared_error')

# Train the model
model.fit(X_train, y_train, epochs=50, batch_size=32, validation_data=(X_test, y_test))

# Predictions
test_predict = model.predict(X_test)

# Evaluate
test_rmse = np.sqrt(mean_squared_error(y_test, test_predict))
print(f'RNN Test RMSE: {test_rmse}')

# Plot predictions
plt.figure(figsize=(14, 7))
plt.plot(df.index[-len(y_test):], df['Adj Close'].iloc[-len(y_test):], label='Actual Prices')
plt.plot(df.index[-len(y_test):], test_predict, label='RNN Predicted Prices')
plt.legend()
plt.show()

### CNN Model ###

# Preprocess data for Quantum CNN
def preprocess_data(df, sequence_length=60):
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(df[['Adj Close']])

    X, y = [], []
    for i in range(sequence_length, len(scaled_data)):
        X.append(scaled_data[i-sequence_length:i])
        y.append(scaled_data[i, 0])

    X, y = np.array(X), np.array(y)
    X = np.reshape(X, (X.shape[0], sequence_length, 1, 1))  # Reshape for CNN input
    X = np.repeat(X, 32, axis=2)  # Increase width to 32 to avoid downsampling issues
    return X, y

X, y = preprocess_data(df)

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

# Quantum node
n_qubits = 4
dev = qml.device("default.qubit", wires=n_qubits)

@qml.qnode(dev)
def quantum_circuit(inputs, weights):
    qml.templates.AngleEmbedding(inputs, wires=range(n_qubits))
    qml.templates.StronglyEntanglingLayers(weights, wires=range(n_qubits))
    return [qml.expval(qml.PauliZ(i)) for i in range(n_qubits)]

weight_shapes = {"weights": (3, n_qubits, 3)}

qlayer = KerasLayer(quantum_circuit, weight_shapes, output_dim=n_qubits)

# Define the Quantum CNN model
model = Sequential()
model.add(Conv2D(32, kernel_size=(3, 3), activation='relu', input_shape=(60, 32, 1)))
model.add(Flatten())
model.add(Dense(n_qubits, activation='relu'))  # Ensure the output matches the number of qubits
model.add(qlayer)
model.add(Dense(1))

# Compile the model
model.compile(optimizer='adam', loss='mean_squared_error')

# Train the model
model.fit(X_train, y_train, epochs=1, batch_size=32, validation_data=(X_test, y_test))

# Predictions
test_predict = model.predict(X_test)

# Evaluate
test_rmse = np.sqrt(mean_squared_error(y_test, test_predict))
print(f'Quantum CNN Test RMSE: {test_rmse}')

# Plot predictions
plt.figure(figsize=(14, 7))
plt.plot(df.index[-len(y_test):], df['Adj Close'].iloc[-len(y_test):], label='Actual Prices')
plt.plot(df.index[-len(y_test):], test_predict, label='Quantum CNN Predicted Prices')
plt.legend()
plt.show()

from sec_edgar_downloader import Downloader

# Initialize the downloader with your email address and a company name
dl = Downloader(email_address="kinghursh.shah@gmail.com", company_name="YourCompanyName")

# Dow Jones Industrial Average companies tickers
dow_jones_stocks = [
    'AAPL', 'MSFT', 'JPM', 'V', 'JNJ', 'WMT', 'PG', 'DIS', 'UNH', 'HD',
    'VZ', 'INTC', 'MRK', 'PFE', 'KO', 'BA', 'CSCO', 'XOM', 'MCD', 'IBM',
    'GS', 'AXP', 'CAT', 'NKE', 'TRV', 'MMM', 'WBA', 'DOW', 'CRM', 'AMGN'
]

# Download 10-K statements for each company
for stock in dow_jones_stocks:
    dl.get("10-K", stock)

print("Downloaded 10-K statements for all companies.")

# Sentiment Analysis on 10-K Statements
sid = SentimentIntensityAnalyzer()

def analyze_sentiment(text):
    return sid.polarity_scores(text)

# Path to the directory where 10-K statements are saved
base_dir = "sec-edgar-filings"

# Collect sentiment scores
sentiments = {}

for stock in dow_jones_stocks:
    stock_dir = os.path.join(base_dir, stock)
    if os.path.exists(stock_dir):
        for root, dirs, files in os.walk(stock_dir):
            for file in files:
                if file.endswith(".txt"):
                    file_path = os.path.join(root, file)
                    print(f"Reading file: {file_path}")
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                        sentiments[stock] = analyze_sentiment(text)
                        print(f"Sentiment for {stock}: {sentiments[stock]}")

# Display the sentiment scores
print("\nSentiment Scores:")
for stock, sentiment in sentiments.items():
    print(f"Sentiment for {stock}: {sentiment}")

### Monte Carlo Simulation ###

def monte_carlo_simulation(start_price, days, mu, sigma, n_simulations=1000):
    simulations = []
    for _ in range(n_simulations):
        prices = [start_price]
        for _ in range(days):
            prices.append(prices[-1] * np.exp(np.random.normal(mu, sigma)))
        simulations.append(prices)
    return simulations

# Parameters
mu = df['Adj Close'].pct_change().mean()
sigma = df['Adj Close'].pct_change().std()
start_price = df['Adj Close'].iloc[-1]

# Run Simulation
n_days = 252
simulations = monte_carlo_simulation(start_price, n_days, mu, sigma)

# Convert to DataFrame
simulations_df = pd.DataFrame(simulations).T
simulations_df['mean'] = simulations_df.mean(axis=1)
simulations_df['lower'] = simulations_df.quantile(0.05, axis=1)
simulations_df['upper'] = simulations_df.quantile(0.95, axis=1)

# Print Summary Statistics
end_prices = simulations_df.iloc[-1, :-3]
mean_price = end_prices.mean()
median_price = end_prices.median()
lower_95 = end_prices.quantile(0.05)
upper_95 = end_prices.quantile(0.95)

print(f"Monte Carlo Simulation Results after {n_days} days:")
print(f"Mean Price: {mean_price:.2f}")
print(f"Median Price: {median_price:.2f}")
print(f"95% Confidence Interval: [{lower_95:.2f}, {upper_95:.2f}]")

# Plot Simulation
plt.figure(figsize=(14,7))
plt.plot(simulations_df)
plt.plot(simulations_df['mean'], label='Mean', color='black', linewidth=2)
plt.plot(simulations_df['lower'], label='95% Confidence Interval (Lower)', color='red', linestyle='--')
plt.plot(simulations_df['upper'], label='95% Confidence Interval (Upper)', color='green', linestyle='--')
plt.xlabel('Days')
plt.ylabel('Price')
plt.title(f"Monte Carlo Simulation for AAPL")
plt.legend()
plt.show()

### Ichimoku Cloud ###

df['tenkan_sen'] = (df['High'].rolling(window=9).max() + df['Low'].rolling(window=9).min()) / 2
df['kijun_sen'] = (df['High'].rolling(window=26).max() + df['Low'].rolling(window=26).min()) / 2
df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(26)
df['senkou_span_b'] = ((df['High'].rolling(window=52).max() + df['Low'].rolling(window=52).min()) / 2).shift(26)
df['chikou_span'] = df['Adj Close'].shift(-26)

plt.figure(figsize=(14,7))
plt.plot(df.index, df['Adj Close'], label='Actual Prices')
plt.plot(df.index, df['senkou_span_a'], label='Senkou Span A', linestyle='--')
plt.plot(df.index, df['senkou_span_b'], label='Senkou Span B', linestyle='--')
plt.fill_between(df.index, df['senkou_span_a'], df['senkou_span_b'], where=(df['senkou_span_a'] > df['senkou_span_b']), color='lightgreen', alpha=0.5)
plt.fill_between(df.index, df['senkou_span_a'], df['senkou_span_b'], where=(df['senkou_span_a'] <= df['senkou_span_b']), color='lightcoral', alpha=0.5)
plt.legend()
plt.show()
import numpy as np
import matplotlib.pyplot as plt

# Sample dataset: features (x) and actual labels (y)
x = np.array([1, 2, 3, 4, 5])  # Input features
y_true = np.array([3, 6, 9, 12, 15])  # Actual values (without noise)

# Add random noise to the true values to simulate real-world data
np.random.seed(42)  # For reproducibility
noise = np.random.normal(0, 1, size=y_true.shape)  # Mean = 0, Standard deviation = 1
y = y_true + noise  # Add noise to the true labels

# Linear regression model: predicted value = w*x + b
# For simplicity, we assume w = 3 and b = 0
w = 3  # Weight
b = 0  # Bias

# Predictions using the linear regression model
y_pred = w * x + b

# 1. Squared Loss (L2 Loss)
squared_loss = (y - y_pred) ** 2
print(f"Squared Loss (L2 Loss): {squared_loss}")

# 2. Mean Squared Error (MSE)
mse = np.mean(squared_loss)
print(f"Mean Squared Error (MSE): {mse}")

# Plotting the actual vs predicted values with noise
plt.scatter(x, y, color='blue', label='Actual values (y)', s=100)
plt.plot(x, y_pred, color='red', label='Predicted values (y_pred)', linewidth=2)
plt.xlabel('x')
plt.ylabel('y')
plt.title('Linear Regression: Actual vs Predicted (with noise)')
plt.legend()
plt.show()


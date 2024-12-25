import matplotlib.pyplot as plt
import numpy as np
import matplotlib.animation as animation


def main():
    # Initialize Dataset
    X = 10*np.random.rand(50)  # 50 random points in the range [0, 10]
    y = 8*X + 1 + 2.5*np.random.randn(50) # Linear relation with noise
    # Create and train the linear regression model
    model = LinearRegression()
    model.train(X,y)

    # Animate the gradient descent process
    model.animate(X,y)

class LinearRegression():
    # Using Gradient Descent for Linear Regression
    """
    Simple Linear Regression model using Gradient Descent
    """
    def __init__(self, learning_rate=0.001, epochs=100):
        """
        Initializes the Linear Regression model.

        Parameters:
        - learning_rate: Step size for gradient descent.
        - epochs: Number of iterations for training.
        """

        self.learning_rate = learning_rate
        self.epochs = epochs
        self.a_0 = 0      # Intercept (bias)
        self.a_1 = 0      # Slope (weight)
        self.w_list = []  # List to store parameters during training

    def train(self, X, y):
        """
        Train the model using Gradient Descent.

        Parameters:
        - X: Input features (independent variable).
        - y: True labels (dependent variable).
        """

        n = X.shape[0]   # Number of data points

        for i in range(self.epochs):
            # Store parameters (weights) at each step
            self.w_list.append([self.a_0,self.a_1])

            # Predictions based on current weights
            y_train = self.a_0 + self.a_1 * X

            # Calculate the error (difference between predictions and actual value
            error = y - y_train        # Whether you use y_train - y or y - y_train will make a difference
            #mse = np.sum(error ** 2) / n   # Mean Squared Error
            mse = np.mean(error ** 2)  # Mean Squared Error

            # Update weights (gradient descent step)

            self.a_0 -= -2/n * np.sum(error) * self.learning_rate
            self.a_1 -= -2/n * np.sum(error * X) * self.learning_rate


            # Update weights (gradient descent step)
            #self.a_0 += 2 * self.learning_rate * np.sum(error) / n
            #self.a_1 += 2 * self.learning_rate * np.sum(error * X) / n

            #if i%10 == 0:
            #   print("MSE",str(i)+":", mse)
            # Optionally print MSE at intervals for debugging (e.g. every 10 epochs)
            if i % 10 == 0:
                print(f"Epoch {i}, MSE: {mse:.4f}")
        self.w_list = np.array(self.w_list)  # Convert to numpy array for easy indexing

    def animate(self, X, y):
        """
        Animate the gradient descent process, showing how the model's fit improves.
        
        Parameters:
        - X: Input features (independent variable).
        - y: True labels (dependent variable).
        """

        fig, ax = plt.subplots()
        ax.scatter(X,y, color='blue', label='Data Points', s=50)
        plot_range = np.array(range(int(min(X))-1,int(max(X))+3))
        a_0,a_1 = self.w_list[0,]
        y_plot = plot_range*a_1 + a_0
        ln, = ax.plot(plot_range, y_plot, color="red", label="Best Fit")

        def animator(frame):
            a_0, a_1 = self.w_list[frame,]
            y_plot = plot_range * a_1 + a_0
            ln.set_data(plot_range,y_plot)


        print("Launching Animation")
        anim = animation.FuncAnimation(fig,func = animator, frames = self.epochs, interval=50)

        # Show the plot with animation
        ax.legend()
        plt.xlabel("X")
        plt.ylabel("y")
        plt.title("Linear Regression Training with Gradient Descent")

        plt.show()

if __name__ == "__main__":
    main()

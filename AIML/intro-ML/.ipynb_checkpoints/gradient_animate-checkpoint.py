import matplotlib.pyplot as plt
import numpy as np
import matplotlib.animation as animation


def main():
    # Initialize Dataset
    X = 10*np.random.rand(50)
    y = 8*X + 1 + 2.5*np.random.randn(50)
    model = LinearRegression()
    model.train(X,y)
    model.animate(X,y)

class LinearRegression():
    # Using Gradient Descent for Linear Regression
    def __init__(self, learning_rate=0.001, epochs=100):
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.a_0 = 0
        self.a_1 = 0
        self.w_list = []

    def train(self, X, y):
        n = X.shape[0]

        for i in range(self.epochs):
            self.w_list.append([self.a_0,self.a_1])
            y_train = self.a_0 + self.a_1 * X
            error = y - y_train        # Whether you use y_train - y or y - y_train will make a difference
            mse = np.sum(error ** 2) / n
            self.a_0 -= -2/n * np.sum(error) * self.learning_rate
            self.a_1 -= -2/n * np.sum(error * X) * self.learning_rate

            #if i%10 == 0:
            #   print("MSE",str(i)+":", mse)
        self.w_list = np.array(self.w_list)

    def animate(self, X, y):
        fig, ax = plt.subplots()
        ax.scatter(X,y)
        plot_range = np.array(range(int(min(X))-1,int(max(X))+3))
        a_0,a_1 = self.w_list[0,]
        y_plot = plot_range*a_1 + a_0
        ln, = ax.plot(plot_range, y_plot, color="red", label="Best Fit")

        def animator(frame):
            a_0, a_1 = self.w_list[frame,]
            y_plot = plot_range * a_1 + a_0
            ln.set_data(plot_range,y_plot)


        print("Launching Animation")
        anim = animation.FuncAnimation(fig,func = animator, frames = self.epochs)
        plt.show()

if __name__ == "__main__":
    main()

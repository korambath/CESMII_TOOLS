import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Function to minize
def f(x):
	return x**2 + 5 * x + 24

# Derivative of the function
def fd(x):
	return 2*x + 5

#x_min = -30
#x_max = 30
x_min = -60
x_max = 60
x = np.linspace(x_min, x_max, 200)
y = f(x)
r = 0.05  # Learning rate
#r = 0.8  # Learning rate
#r = 1.0  # Learning rate
learning_rates = [0.05, 0.8, 1.0]  # List of dynamic learning rates
x_est = 35  # Starting point
y_est = f(x_est)


# Maximum number of steps per animation cycle
max_steps = 100


def animate(i):
	global x_est
	global y_est

	# Gradient descent
	x_est = x_est - fd(x_est) * r
	y_est = f(x_est)

	# Update the plot
	scat.set_offsets([[x_est,y_est]])
	text.set_text("Value : %.2f" % y_est)
	line.set_data(x, y)


        # Reset the gradient descent path after max_steps
	if i == max_steps - 1:
            x_est = 35  # Reset to starting point
            y_est = f(x_est)



	return line, scat, text

def init():
	line.set_data([], [])
	return line,

# Visualization Stuff
fig, ax = plt.subplots()
ax.set_xlim([x_min, x_max])
ax.set_ylim([-15, 1500])
ax.set_xlabel("x")
ax.set_ylabel("f(x)")
plt.title("Gradient Descent")
line, = ax.plot([], [])
scat = ax.scatter([], [], c="red")
text = ax.text(-25,1300,"")

#ani = animation.FuncAnimation(fig, animate, 100, init_func=init, interval=100, blit=True)
ani = animation.FuncAnimation(fig, animate, max_steps, init_func=init, interval=100, blit=True, repeat=True)

plt.show()

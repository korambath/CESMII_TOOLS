import matplotlib.pyplot as plt
import matplotlib.image as mpimg

# Read the image file
image = mpimg.imread("cat_and_otter.png")

# Display the image
plt.imshow(image)
plt.show()

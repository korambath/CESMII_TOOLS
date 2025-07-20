import pygame
# Initialize Pygame and the mixer
pygame.init()
pygame.mixer.init()

# Load the sound effect (replace 'path/to/your/sound.wav' with your file)

sound = pygame.mixer.Sound('out.wav')
# Play the sound effect
sound.play()

# Keep the program running long enough for the sound to play
# In a full game, you would have a game loop handling this.
pygame.time.wait(2000) # waits for 2 seconds

# Quit Pygame
pygame.quit()



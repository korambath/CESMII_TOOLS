import pygame

# Initialize Pygame and the mixer
pygame.init()
pygame.mixer.init()

# Load the music file (replace 'path/to/your/music.mp3' with your file)
# MP3, OGG, MOD, XM are commonly supported for music.
pygame.mixer.music.load('outg.wav')

# Play the music (0 for playing once, -1 for infinite loop)
pygame.mixer.music.play(-1) 

# You can also set the volume (0.0 to 1.0)
pygame.mixer.music.set_volume(0.5)

# Keep the program running long enough for the music to play
# In a full game, you would have a game loop handling this.
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

# Stop the music when done
pygame.mixer.music.stop()

# Quit Pygame
pygame.quit()

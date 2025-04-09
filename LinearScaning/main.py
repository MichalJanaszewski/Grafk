import pygame
from constants import *
from prism import Prism
from renderer import Renderer
from camera import Camera

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    camera = Camera()
    prisms = Prism.load_prisms_from_file("prisms.json")
    renderer = Renderer(screen, camera, prisms)

    renderer.render()

    key_map = {
        pygame.K_LEFT: lambda: camera.rotate(1, -ROT_SPEED['y']),
        pygame.K_RIGHT: lambda: camera.rotate(1, ROT_SPEED['y']),
        pygame.K_UP: lambda: camera.rotate(0, -ROT_SPEED['x']),
        pygame.K_DOWN: lambda: camera.rotate(0, +ROT_SPEED['x']),
        pygame.K_z: lambda: camera.rotate(2, ROT_SPEED['z']),
        pygame.K_c: lambda: camera.rotate(2, -ROT_SPEED['z']),
        pygame.K_w: lambda: shift_prisms(prisms, camera.translate(0, 0, MOVE_SPEED)),
        pygame.K_s: lambda: shift_prisms(prisms, camera.translate(0, 0, -MOVE_SPEED)),
        pygame.K_a: lambda: shift_prisms(prisms, camera.translate(MOVE_SPEED, 0, 0)),
        pygame.K_d: lambda: shift_prisms(prisms, camera.translate(-MOVE_SPEED, 0, 0)),
        pygame.K_q: lambda: shift_prisms(prisms, camera.translate(0, MOVE_SPEED, 0)),
        pygame.K_e: lambda: shift_prisms(prisms, camera.translate(0, -MOVE_SPEED, 0)),
        pygame.K_EQUALS: lambda: camera.zoom(-ZOOM_STEP),
        pygame.K_MINUS: lambda: camera.zoom(ZOOM_STEP),
    }

    key_states = {
        key: {
            "pressed": False,
            "start_time": 0,
            "last_repeat": 0
        } for key in key_map
    }

    running = True
    while running:
        dt = clock.tick(60)
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in key_map and not key_states[event.key]["pressed"]:
                    key_map[event.key]()
                    key_states[event.key]["pressed"] = True
                    key_states[event.key]["start_time"] = current_time
                    key_states[event.key]["last_repeat"] = current_time
                    renderer.render()
            elif event.type == pygame.KEYUP:
                if event.key in key_states:
                    key_states[event.key]["pressed"] = False

        keys = pygame.key.get_pressed()
        any_action = False

        for key, state in key_states.items():
            if state["pressed"] and keys[key]:
                if current_time - state["start_time"] > HOLD_START_DELAY:
                    if current_time - state["last_repeat"] > HOLD_REPEAT_INTERVAL:
                        key_map[key]()
                        state["last_repeat"] = current_time
                        any_action = True

        if any_action:
            renderer.render()

    pygame.quit()

def shift_prisms(prisms, vec):
    for prism in prisms:
        prism.position += vec

if __name__ == "__main__":
    main()
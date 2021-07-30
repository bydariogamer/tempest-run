import pygame

import config
import main
import gameplay.player2d as player2d
import gameplay.levels as levels
import rendering.neon as neon
import rendering.threedee as threedee
import rendering.levelbuilder3d as levelbuilder3d
import keybinds
import util.utility_functions as utility_functions
import config


class GameplayMode(main.GameMode):

    def __init__(self, loop):
        super().__init__(loop)
        self.player = player2d.Player()
        self.current_level = levels.InfiniteGeneratingLevel(9)

        self.camera = threedee.Camera3D()
        self.camera.position.y = -1
        self.camera_z_offset = -40
        self.unload_offset = -30

        self.foresight = 150
        self.neon_renderer = neon.NeonRenderer()

    def update(self, dt, events):
        cur_z = self.player.z
        self.player.set_speed(self.current_level.get_player_speed(cur_z))
        self.player.update(dt)
        self.handle_events(events)
        # TODO check for collisions and stuff

        self.camera.position.z = self.player.z + self.camera_z_offset
        self.current_level.unload_obstacles(self.camera.position.z + self.unload_offset)

    def handle_events(self, events):
        if events is None:
            return
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in keybinds.JUMP:
                    self.player.jump()
                if e.key in keybinds.LEFT:
                    self.player.move_left()
                if e.key in keybinds.RIGHT:
                    self.player.move_right()
                if e.key in keybinds.SLIDE:
                    self.player.slide()
                if e.key == pygame.K_ESCAPE:
                    self.loop.push_next_mode(PauseMenu(self.loop))
            if e.type == pygame.KEYUP:
                if e.key in keybinds.SLIDE:
                    self.player.set_mode('run')

    def draw_to_screen(self, screen, extra_darkness_factor=1):
        screen.fill((0, 0, 0))
        all_lines = []
        cell_length = self.current_level.get_cell_length()
        z = self.camera.position.z
        n_lanes = self.current_level.number_of_lanes()
        cell_start = int(z / cell_length)
        cell_end = int((z + self.foresight) / cell_length + 1)

        for i in range(cell_start, cell_end):
            all_lines.extend(levelbuilder3d.build_section(i * cell_length, cell_length, self.current_level))

        for n in range(n_lanes):
            obstacles = self.current_level.get_all_obstacles_between(n, z, z + self.foresight)
            for obs in reversed(obstacles):
                # add them from from back to front so they overlap properly
                all_lines.extend(levelbuilder3d.build_obstacle(obs, self.current_level))

        all_lines.extend(levelbuilder3d.get_player_shape(self.player, self.current_level))

        all_2d_lines = self.camera.project_to_surface(screen, all_lines)
        neon_lines = neon.NeonLine.convert_line2ds_to_neon_lines(all_2d_lines)

        self.neon_renderer.draw_lines(screen, neon_lines, extra_darkness_factor=extra_darkness_factor)


class PauseMenu(main.GameMode):
    def __init__(self, loop):
        super().__init__(loop)
        self.selected_option_idx = 0
        self.options = [
            ("continue", lambda: self.continue_pressed()),
            ("exit", lambda: self.exit_pressed())
        ]

        self.title_font = pygame.font.Font("assets/fonts/CONSOLA.TTF", config.TITLE_SIZE)
        self.option_font = pygame.font.Font("assets/fonts/CONSOLA.TTF", config.OPTION_SIZE)

        self.pause_timer = 0  # how long we've been paused

    def update(self, dt, events):
        self.pause_timer += dt
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in keybinds.MENU_UP:
                    # TODO play menu blip sound
                    self.selected_option_idx = (self.selected_option_idx - 1) % len(self.options)
                elif e.key in keybinds.MENU_DOWN:
                    # TODO play menu blip sound
                    self.selected_option_idx = (self.selected_option_idx + 1) % len(self.options)
                elif e.key in keybinds.MENU_ACCEPT:
                    self.options[self.selected_option_idx][1]()  # activate the option's lambda
                    return
                elif e.key in keybinds.MENU_CANCEL:
                    self.continue_pressed()
                    return

    def continue_pressed(self):
        self.state = -1

    def exit_pressed(self):
        import main
        self.loop.set_mode_and_clear_stack(main.MainMenuMode(self.loop))

    def draw_to_screen(self, screen):
        # make the level underneath fade darker slightly after you've paused
        max_darkness = 0.333
        max_darkness_time = 0.1  # second
        current_darkness = utility_functions.lerp(self.pause_timer / max_darkness_time, 1, max_darkness)

        # drawing level underneath this menu
        self.loop.modes[-2].draw_to_screen(screen, extra_darkness_factor=current_darkness)

        screen_size = screen.get_size()
        title_surface = self.title_font.render('PAUSE', True, neon.WHITE)

        title_size = title_surface.get_size()
        title_y = screen_size[1] // 3 - title_size[1] // 2
        screen.blit(title_surface, dest=(screen_size[0] // 2 - title_size[0] // 2, title_y))

        option_y = max(screen_size[1] // 2, title_y + title_size[1])
        for i in range(len(self.options)):
            option_text = self.options[i][0]
            is_selected = i == self.selected_option_idx
            color = neon.WHITE if not is_selected else neon.ORANGE

            option_surface = self.option_font.render(option_text, True, color)
            option_size = option_surface.get_size()
            screen.blit(option_surface, dest=(screen_size[0] // 2 - option_size[0] // 2, option_y))
            option_y += option_size[1]

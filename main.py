import pygame

import keybinds
import rendering.neon as neon
import config
import util.profiling as profiling

TARGET_FPS = config.BASE_FPS if not config.TESTMODE else -1

# this is only the default size, use pygame.display.get_surface().get_size() to get the current size.
W, H = config.DISP_WID, config.DISP_HEI


class GameLoop:

    def __init__(self):
        self.running = True
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.get_surface()
        self.modes = [MainMenuMode(self)]

    def push_next_mode(self, next_mode):
        self.modes.append(next_mode)

    def pop_current_mode(self):
        return self.modes.pop(-1)

    def set_mode_and_clear_stack(self, next_mode):
        self.modes = [next_mode]

    def start(self):
        dt = 0
        while self.running:
            events = []
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    print("INFO: quitting game")
                    self.running = False
                    return
                else:
                    # collect all the events so we can pass them into the current game mode.
                    events.append(e)

                # global keybinds
                if e.type == pygame.KEYDOWN:
                    if e.key in keybinds.TOGGLE_NEON:
                        config.USE_NEON = not config.USE_NEON
                        print("INFO: toggling neon to: {}".format(config.USE_NEON))
                    if e.key in keybinds.TOGGLE_PROFILER:
                        profiling.get_instance().toggle()

            if self.modes[-1].state == 0:
                self.modes[-1].on_mode_start()
                self.modes[-1].state = 1
            elif self.modes[-1].state == -1:
                self.modes[-1].on_mode_end()
                self.modes.pop()

            self.modes[-1].update(dt, events)
            self.modes[-1].draw_to_screen(self.screen)
            pygame.display.flip()

            if config.TESTMODE:
                pygame.display.set_caption(f"TEMPEST RUN {int(self.clock.get_fps())} FPS")

            dt = self.clock.tick(TARGET_FPS) / 1000.0


class GameMode:

    def __init__(self, loop: GameLoop):
        self.loop: GameLoop = loop
        self.state = 0

    def on_mode_start(self):
        """Called when mode becomes active"""
        pass

    def on_mode_end(self):
        """Called when mode becomes inactive"""
        pass

    def update(self, dt, events):
        pass

    def draw_to_screen(self, screen):
        pass


class MainMenuMode(GameMode):

    def __init__(self, loop: GameLoop):
        super().__init__(loop)
        self.song = pygame
        self.selected_option_idx = 0
        self.options = [
            ("start", lambda: self.start_pressed()),
            ("help", lambda: self.help_pressed()),
            ("credits", lambda: self.credits_pressed()),
            ("exit", lambda: self.exit_pressed())
        ]

        self.title_font = pygame.font.Font("assets/fonts/CONSOLA.TTF", config.TITLE_SIZE)
        self.option_font = pygame.font.Font("assets/fonts/CONSOLA.TTF", config.OPTION_SIZE)

    def on_mode_start(self):
        # TODO song
        pass

    def start_pressed(self):
        import gameplay.gamestuff  # shh don't tell pylint about this
        self.loop.set_mode_and_clear_stack(gameplay.gamestuff.GameplayMode(self.loop))

    def help_pressed(self):
        import menus.help_menu as help_menu
        self.loop.push_next_mode(help_menu.HelpMenuMode(self.loop))

    def credits_pressed(self):
        # TODO add credits menu
        pass

    def exit_pressed(self):
        self.loop.running = False

    def update(self, dt, events):
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
                    self.exit_pressed()
                    return

    def draw_to_screen(self, screen: pygame.Surface):
        screen.fill((0, 0, 0))
        screen_size = screen.get_size()
        title_surface = self.title_font.render('TEMPEST RUN', True, neon.WHITE)

        title_size = title_surface.get_size()
        title_y = screen_size[1] // 3 - title_size[1] // 2
        screen.blit(title_surface, dest=(screen_size[0] // 2 - title_size[0] // 2,
                                         title_y))

        option_y = max(screen_size[1] // 2, title_y + title_size[1])
        for i in range(len(self.options)):
            option_text = self.options[i][0]
            is_selected = i == self.selected_option_idx
            color = neon.WHITE if not is_selected else neon.RED

            option_surface = self.option_font.render(option_text, True, color)
            option_size = option_surface.get_size()
            screen.blit(option_surface, dest=(screen_size[0] // 2 - option_size[0] // 2, option_y))
            option_y += option_size[1]


if __name__ == "__main__":
    pygame.init()
    pygame.display.set_mode((W, H), pygame.SCALED | pygame.RESIZABLE)
    pygame.display.set_caption("TEMPEST RUN")
    loop = GameLoop()
    loop.start()

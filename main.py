import thread
import random
from copy import copy
from kivy.app import App
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.factory import Factory 
from kivy.garden.progressspinner import ProgressSpinner
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.widget import Widget 

from fixedlayout import FixedLayout, FixedLayoutRoot, FixedImage,\
    FixedImageButton, FixedPopup, FixedRadioButtons, FixedSimpleMenu,\
    FixedSimpleMenuItem, FixedButton

from simplestate import StateMachine, State
from gameengine import KalahGame
from characters import AI_LIST

__version__ = '0.0.6'

machine = StateMachine(debug=True)

seeds = None

USER = 1
AI = 2

PARKED = (2000, 2000)
HAND = 0

#############################
#
#  SETTINGS
#
#############################

settings = {
    "ai_chosen": 0,
    "who_plays_first": 0,
    "first_player": USER,
    "seeds_per_house_selection": 1,
    "seeds_per_house": 4,
    "capture_rule": 0,
    "eog_rule": 0,
    "seed_drop_rate": 0.4,
}
character = AI_LIST[settings['ai_chosen']]

visual_settings = {
    "who_plays_first": [
        "You",
        "Opponent (AI)"
    ],
    "seeds_per_house_selection": [
        "3",
        "4",
        "5",
        "6"
    ],
    "capture_rule": [
        "Capture if opposite house has seeds",
        "Always capture (even if opposite empty)",
        "Never allow capture"
    ],
    "eog_rule": [
        "Move seeds to the store/Kalaha on that side",
        "Move seeds to the player with empty houses",
        "Move seeds to the player that ended the game",
        "Leave the seeds in the houses"
    ],
}

def update_setting(setting_name, value):
    global settings
    global visual_settings
    global character
    global app

    settings[setting_name] = value
    if setting_name == "ai_chosen":
        settings["ai_chosen"] = value
        character = AI_LIST[value]
        print "CHARACTER", character
        return
    if setting_name == "who_plays_first":
        if value == 0:
            settings["first_player"] = USER
        else:
            settings["first_player"] = AI
    if setting_name == "seeds_per_house_selection":
        settings["seeds_per_house"] = value + 3
    if setting_name not in visual_settings:
        return
    app.root.screens[SETTINGS_RULES_SCREEN].ids.rules_screen_menu.\
        set_text(setting_name, visual_settings[setting_name][value])
    print "SETTINGS", settings

def generically_apply_settings():
    global settings

    for key in settings:
        update_setting(key, settings[key])


##############################
#
#  KIVY CLASSES
#
##############################

GAME_SCREEN = 0
SETTINGS_OPPONENT_SCREEN = 1
SETTINGS_RULES_SCREEN = 2
SETTINGS_SCREEN_SCREEN = 3
SETTINGS_SOUND_SCREEN = 4

class GameScreen(Screen):
    global machine

    HANDS = [
        {}, # 0, nobody
        {"pos": (500, 0)},       # 1 user
        {"pos": (500, 1080)}     # 2 ai
    ]

    PITS = [
        {"pos": PARKED     }, #  0, hand
        {"pos": (430,  350)}, #  1
        {"pos": (640,  350)}, #  2
        {"pos": (850,  350)}, #  3
        {"pos": (1060, 350)}, #  4
        {"pos": (1270, 350)}, #  5
        {"pos": (1480, 350)}, #  6
        {"pos": (1690, 350)}, #  7 user store
        {"pos": (1480, 770)}, #  8
        {"pos": (1270, 770)}, #  9
        {"pos": (1060, 770)}, # 10
        {"pos": (850,  770)}, # 11
        {"pos": (640,  770)}, # 12
        {"pos": (430,  770)}, # 13
        {"pos": (220,  770)}  # 14 ai store
    ]

    def pushed_pit(self, pit):
        machine.input("pushed_pit", pit)


class SettingsOpponentScreen(Screen):

    global settings
    global character
    global AI_LIST
    
    def _update_details(self, ai_chosen):
        update_setting("ai_chosen", ai_chosen)
        self.ids.ai_description.text = character['desc']
        self.ids.ai_play_style.text = character['tagline']
        self.ids.ai_name.text = format("{} of 12: [size=80]{}[/size]").format(
            character['rank'],
            character['name']
        )
        # self.ids.ai_face_image

    def previous_ai(self):
        ai_chosen = (settings['ai_chosen'] - 1) % 12
        settings['ai_chosen'] = ai_chosen
        self._update_details(ai_chosen)

    def next_ai(self):
        ai_chosen = (settings['ai_chosen'] + 1) % 12
        settings['ai_chosen'] = ai_chosen
        self._update_details(ai_chosen)

class SettingsRulesScreen(Screen):
    pass


class SettingsScreenScreen(Screen):
    pass


class SettingsSoundScreen(Screen):
    pass


class AppScreenManager(ScreenManager):
    pass

class MancalaApp(App):

    def build(self):
        presentation = Builder.load_file('mancala.kv')

    def on_start(self):
        machine.bind_reference("kivy", self.root.screens[GAME_SCREEN].ids)
        machine.change_state("init_game")
        generically_apply_settings()

    def start_new_game(self):
        self.root.current = "game_screen"
        machine.input("request_new_game")


##############################
#
#  ANIMATION
#
##############################

class Seeds(object):

    global HAND

    def __init__(self, display):
        self.board = [[] for x in xrange(15)]
        for index in range(4*12):
            seed = display["seed,{}".format(index)]
            self.board[HAND].append(seed)
        self.display = display

    def scoop(self, pit):
        seed_count = len(self.board[pit])
        for _ in range(seed_count):
            seed = self.board[pit].pop()
            self.board[HAND].append(seed)
            self._move(seed, HAND)

    def drop(self, pit, count):
        for _ in range(count):
            seed = self.board[HAND].pop()
            self.board[pit].append(seed)
            self._move(seed, pit)

    def _move(self, seed, pit):
        pos_hint = GameScreen.PITS[pit]['pos']
        x = pos_hint[0] + random.randint(-50, 50)
        y = pos_hint[1] + random.randint(-50, 50)
        seed.pos_hint = (x, y)



class HandSeedAnimation(object):

    global seeds
    global settings

    def __init__(self, player, board, display, clear_first=False):
        self.nplayer = player
        self.idx = 0
        self.board = copy(board)
        self.display = display
        self.animation_steps = game.animate
        self.animation_steps.append({"action": "home"})
        self.last_step = {}
        if player==USER:
            self.hand = display.user_hand
        else:
            self.hand = display.ai_hand
        if clear_first:
            for pit in range(1, 15):
                seeds.scoop(pit)
        self.play_one_step(None, None)

    def play_one_step(self, sequence, widget):
        if self.idx<len(self.animation_steps):
            # CLEAN UP AFTER LAST STEP
            action = self.last_step.get('action')
            pit = self.last_step.get('loc')
            count = self.last_step.get('count')
            if action=="scoop":
                self.board[pit] = 0
                seeds.scoop(pit)
            elif action=="drop":
                self.board[pit] += count
                seeds.drop(pit, count)
            elif action=="drop_all":
                self.board[pit] += count
                seeds.drop(pit, count)
            elif action=="steal":
                pass
            elif action=="game_over":
                pass
            elif action=="normal_move":
                pass
            elif action=="home":
                pass
            # ACT ON NEW STEP
            step = self.animation_steps[self.idx]
            action = step['action']
            pit = step.get('loc')
            count = step.get('count')
            hand_animation = None # everything is timed by hand movement
            if step['action']=="scoop":
                hand_animation = Animation(
                    pos_hint=GameScreen.PITS[pit]["pos"],
                    duration=settings['seed_drop_rate'],
                    t='in_out_sine'
                )
            elif step['action']=="drop":
                hand_animation = Animation(
                    pos_hint=GameScreen.PITS[pit]["pos"],
                    duration=settings['seed_drop_rate'],
                    t='in_out_sine'
                )
            elif step['action']=="drop_all":
                hand_animation = Animation(
                    pos_hint=GameScreen.PITS[pit]["pos"],
                    duration=settings['seed_drop_rate'],
                    t='in_out_sine'
                )
            elif step['action']=="steal":
                self.display.center_message.text = "Stealing!"
            elif step['action']=="game_over":
                self.display.center_message.text = "Handling End of Game"
            elif step['action']=="setting_up":
                self.display.center_message.text = "Setting Up Board"
            elif step['action']=="normal_move":
                self.display.center_message.text = ""
            elif step['action']=="home":
                self.display.center_message.text = ""
                hand_animation = Animation(
                    pos_hint = GameScreen.HANDS[self.nplayer]['pos'],
                    duration=settings['seed_drop_rate'],
                    t='in_out_sine'
                )
            # update_numbers
            display_board(self.board, self.display)
            if not hand_animation:
                hand_animation = Animation(pos_hint=self.hand.pos_hint)
            hand_animation.bind(on_complete = self.play_one_step)
            hand_animation.start(self.hand)
            self.idx += 1
            self.last_step = step
        else:
            machine.input("animation_done")


##############################
#
#  SIMPLE STATE CLASSES
#
##############################

class PendingStartState(State):
    
    global settings

    def on_exit(self):
        global seeds
        self.ref['game'].board = [settings["seeds_per_house"]*12] + [0]*14
        seeds = Seeds(self.ref["kivy"])

class InitGameState(State):

    def on_entry(self):
        self.ref['kivy'].wait_on_ai.stop_spinning()
        board_prior = copy(self.ref["game"].board)
        self.ref["game"].reset_board()
        if any([board_prior[i] for i in range(1, 15)]):
            self.animation = HandSeedAnimation(AI, board_prior, self.ref['kivy'], clear_first=True)
        else:
            self.animation = HandSeedAnimation(AI, board_prior, self.ref['kivy'])
        return self.same_state

    def input(self, input_name, *args, **kwargs):
        if input_name=="animation_done":
            return self.change_state("start_turn")
        if input_name == "request_new_game":
            self.change_state("init_game")


def grab(alist, index):
    try:
        return alist[index]
    except IndexError:
        return None

def display_board(board, kivy_ids):
    for pit, count in enumerate(board):
        if pit > 0:
            pit_id = "counter,{}".format(pit)
            kivy_ids[pit_id].text = str(count)

class StartTurn(State):

    def on_entry(self):
        self.ref["choices_so_far"] = []
        self.ref["ai_choices"] = []
        if self.ref["game"].is_over():
            return self.change_state("eog")
        if self.ref["game"].nplayer==1:
            self.ref["kivy"].center_message.text = "Player, choose a house."
            self.ref["game"].usermove_start_simulation()
            self.ref["possible_user_moves"] = self.ref["game"].possible_moves()
            return self.change_state("wait_for_pit")
        return self.change_state("ai_thinking")

    def input(self, input_name, *args, **kwargs):
        if input_name == "request_new_game":
            self.change_state("init_game")

class WaitForPitButtons(State):

    def on_entry(self):
        display_board(self.ref['game'].board, self.ref['kivy'])

    def input(self, input_name, *args, **kwargs):
        if input_name=="pushed_pit":
            pit = args[0]
            index = len(self.ref['choices_so_far'])
            valid_move = any(grab(chlist, index)==pit for chlist in self.ref["possible_user_moves"])
            if valid_move:
                self.ref['kivy'].center_message.text = "playing house {}".format(pit)
                self.ref['choices_so_far'].append(pit)
                self.change_state("animate_user")
            else:
                self.ref['kivy'].center_message.text = "cannot play empty house. try again."
        if input_name == "request_new_game":
            self.change_state("init_game")

class AnitmateUserChoiceState(State):

    def on_entry(self):
        board_prior = copy(self.ref["game"].board)
        self.ref["game"].usermove_simulate_choice(self.ref['choices_so_far'])
        self.animation = HandSeedAnimation(USER, board_prior, self.ref['kivy'])

    def input(self, input_name, *args, **kwargs):
        if input_name=="animation_done":
            possible_moves = self.ref["possible_user_moves"]
            done = any([chlist==self.ref['choices_so_far'] for chlist in possible_moves])
            if done:
                self.ref["game"].usermove_finish_simulation()
                self.ref["game"].play_move(self.ref['choices_so_far'])
                return self.change_state("start_turn")
            self.ref['kivy'].center_message.text ="landed in store. play again."
            return self.change_state("wait_for_pit")
        if input_name == "request_new_game":
            self.change_state("init_game")

    def on_exit(self):
        display_board(self.ref['game'].board, self.ref['kivy'])


def get_ai_move():
    global game
    global machine
    choices = game.get_move()
    machine.input("ai_move", choices)


class AIThinkingState(State):
    
    def on_entry(self):
        self.ref['kivy'].center_message.text = "AI is thinking"
        self.ref['kivy'].wait_on_ai.start_spinning()
        thread.start_new_thread(get_ai_move, ())

    def input(self, input_name, *args, **kwargs):
        if input_name == "ai_move":
            self.ref["ai_choices"] = args[0]
            self.ref["kivy"].wait_on_ai.stop_spinning()
            self.change_state("animate_ai")
        if input_name == "request_new_game":
            self.change_state("init_game")

class AnimateAIChoicesState(State):

    def on_entry(self):
        board_prior = copy(self.ref['game'].board)
        self.ref['game'].play_move(self.ref['ai_choices'])
        self.animation = HandSeedAnimation(AI, board_prior, self.ref['kivy'])

    def input(self, input_name, *args, **kwargs):
        if input_name=="animation_done":
            self.change_state('start_turn')
        if input_name == "request_new_game":
            self.change_state("init_game")

    def on_exit(self):
        display_board(self.ref['game'].board, self.ref['kivy'])

class EndOfGameDisplayState(State):

    def on_entry(self):
        winner = self.ref['game'].get_winner()    
        self.ref["kivy"].center_message.text = ["Tie Game.", "You won!", "AI won."][game.get_winner()]

    def input(self, input_name, *args, **kwargs):
        if input_name == "request_new_game":
            self.change_state("init_game")


if __name__=='__main__':
    game = KalahGame(settings, character)
    machine.bind_reference("game", game)
    machine.bind_reference("settings", settings)
    machine.register_state(StartTurn("start_turn"))
    machine.register_state(PendingStartState("pending_start"))
    machine.register_state(InitGameState("init_game"))
    machine.register_state(WaitForPitButtons("wait_for_pit"))
    machine.register_state(AnitmateUserChoiceState("animate_user"))
    machine.register_state(AIThinkingState("ai_thinking"))
    machine.register_state(AnimateAIChoicesState("animate_ai"))
    machine.register_state(EndOfGameDisplayState("eog"))
    machine.start("pending_start")
    app = MancalaApp()
    app.run()

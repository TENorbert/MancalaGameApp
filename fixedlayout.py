from kivy.uix.layout import Layout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import OptionProperty, VariableListProperty, ObjectProperty,\
    NumericProperty, ReferenceListProperty, ListProperty, StringProperty, BooleanProperty
from kivy.core.window import Window
from kivy.uix.behaviors.button import ButtonBehavior
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line
from kivy.config import Config

from functools import partial

X = 0
Y = 1
WIDTH = 0
HEIGHT = 1

def grab(alist, index):
    try:
        return alist[index]
    except IndexError:
        return None

class FixedProperties(object):

    true_screen_size = VariableListProperty([1920, 1080], limit=2)
    # initial sizing somewhat inspired by Google Material
    true_title_font_size = NumericProperty(80.0)
    true_subheading_font_size = NumericProperty(64.0)
    true_font_size = NumericProperty(56.0)
    #
    pos_fixed = ObjectProperty((0,0))
    size_fixed = ObjectProperty((1920, 1080))
    spot_fixed = ObjectProperty((0,0))
    #
    active_pos_fixed = ObjectProperty((0,0))


class FixedBase(FixedProperties):

    def __init__(self, *args, **kwargs):
        return

    # # this routine is replaced by parent or override
    # def scale_size(self, xy_tuple):
    #     return [1.0, 1.0]

    # # this routine is generally replaced by parent or override
    # def scale_pos(self, xy_tuple, xy_offset):
    #     return {'x': 0.0, 'y': 0.0}

    def scale_size(self, *args):
        return self.parent.scale_size(*args)

    def scale_pos(self, *args):
        return self.parent.scale_pos(*args)

    def super_size_me(self, obj, value):
        print "SUPER SIZE ME FIXED BASE"
        return self.parent.super_size_me(obj, value)

    # deprecate
    def true_scaler(self, value):
        return 1.0

    # def on_parent(self, instance, value):
    #     if hasattr(self.parent, "scale_size"):
    #         self.scale_size = self.parent.scale_size
    #     if hasattr(self.parent, "scale_pos"):
    #         self.scale_pos = self.parent.scale_pos

    # def add_widget(self, widget, index=0):
    #     if not hasattr(widget, "pos_fixed"):
    #         widget.apply_property(pos_fixed=ObjectProperty((0, 0)))
    #     if not hasattr(widget, "size_fixed"):
    #         widget.apply_property(size_fixed=ObjectProperty((100, 100)))
    #     if not hasattr(widget, "spot_fixed"):
    #         widget.apply_property(spot_fixed=ObjectProperty((0, 0)))
    #     widget.bind(
    #        pos_fixed=self.super_size_me
    #     )
    #     widget.bind(
    #        size_fixed=self.super_size_me
    #     )
    #     widget.bind(
    #        spot_fixed=self.super_size_me
    #     )
    #     # return super(FixedBase, self).add_widget(widget, index)

    # def remove_widget(self, widget):
    #     return super(FixedBase, self).remove_widget(widget)


class FixedLayout(FloatLayout, FixedProperties):

    def __init__(self, **kwargs):
        self.pcnt_per_pixel = [0.1, 0.1]
        self.pcnt_margin = [0.0, 0.0]
        super(FixedLayout, self).__init__(**kwargs)
        fbind = self.fbind
        update = self._trigger_layout
        fbind('size', update)
        fbind('pos', update)
        self.calc_scale_to_window()

    def calc_scale_to_window(self, *args, **kwargs):
        # the goal here, is to figure out the percentage per-pixel to map
        #    pos_fixed or size_fixed into pos_hint and size_hint
        self.window_width, self.window_height = self.size
        wh = float(self.window_height)
        ww = float(self.window_width)
        sh = float(self.true_screen_size[HEIGHT])
        sw = float(self.true_screen_size[WIDTH])
        screen_ratio = sw/sh
        window_ratio = ww/wh
        if screen_ratio < window_ratio:
            overall_width = (sw / (sh / wh)) / ww
            overall_height = 1.0
        else:
            overall_width = 1.0
            overall_height = (sh / (sw / ww)) / wh
        overall_margin_width = (1.0 - overall_width) / 2.0
        overall_margin_height = (1.0 - overall_height) / 2.0
        self.pcnt_per_pixel[WIDTH] = overall_width / sw
        self.pcnt_per_pixel[HEIGHT] = overall_height / sh
        self.pcnt_margin[WIDTH] = overall_margin_width
        self.pcnt_margin[HEIGHT] = overall_margin_height

    def true_scaler(self, value):
        if not value:
            return 0
        return value * self.pcnt_per_pixel[HEIGHT]

    def scale_size(self, xy_tuple):
        if not xy_tuple:
            xy_tuple=(0, 0)
        x, y = xy_tuple
        pcnt = [1, 1]
        pcnt[X] = x * self.pcnt_per_pixel[WIDTH]
        pcnt[Y] = y * self.pcnt_per_pixel[HEIGHT]
        return pcnt

    def scale_pos(self, xy_tuple, xy_offset):
        if not xy_tuple:
            xy_tuple=(0, 0)
        x, y = xy_tuple
        xo, yo = xy_offset
        pcnt = {}
        pcnt['x'] = (x - xo) * self.pcnt_per_pixel[WIDTH] + self.pcnt_margin[WIDTH]
        pcnt['y'] = (y - yo) * self.pcnt_per_pixel[HEIGHT] + self.pcnt_margin[HEIGHT]
        return pcnt

    def do_layout(self, *args, **kwargs):
        self.calc_scale_to_window()
        for c in self.children:
            self.process_child(c)
            # if isinstance(c, FixedBase):
            #     for sub in c.children:
            #         self.process_child(sub)
        super(FixedLayout, self).do_layout(*args, **kwargs)

    def process_child(self, c):
        #
        # handle size
        #
        s = self.scale_size(c.size_fixed)
        c.size_hint_x = s[WIDTH]
        c.size_hint_y = s[HEIGHT]
        #
        # handle position
        #
        if hasattr(c, "spot_fixed"):
            c.pos_hint = self.scale_pos(c.pos_fixed, c.spot_fixed)
        # if 'true_font_size' in dir(c):
        #     c.font_size = self.true_scaler(c.true_font_size)

    def super_size_me(self, instance, value):
        self.process_child(instance)
        print "SUPER SIZE ", instance, instance.pos_fixed

    def add_to_root(self, widget):
        self.add_widget(widget)

    def delete_from_root(self, widget):
        self.remove_widget(widget)

    # we override the FixedBase version because FixedLayout is the parent
    def add_widget(self, widget, index=0):
        if not hasattr(widget, "pos_fixed"):
            widget.apply_property(pos_fixed=ObjectProperty((0, 0)))
        if not hasattr(widget, "size_fixed"):
            widget.apply_property(size_fixed=ObjectProperty((100, 100)))
        if not hasattr(widget, "spot_fixed"):
            widget.apply_property(spot_fixed=ObjectProperty((0, 0)))
        if not hasattr(widget, "active_pos_fixed"):
            widget.apply_property(active_pos_fixed=ObjectProperty((0, 0)))
        widget.bind(
           pos_fixed=self._trigger_layout
        )
        widget.bind(
           size_fixed=self._trigger_layout
        )
        widget.bind(
           spot_fixed=self._trigger_layout
        )
        widget.add_to_root = self.add_to_root
        widget.delete_from_root = self.delete_from_root
        return FloatLayout.add_widget(self, widget, index)

    def remove_widget(self, widget):
        widget.unbind(
            spot_fixed=self._trigger_layout
        )
        widget.unbind(
            size_fixed=self._trigger_layout
        )
        widget.unbind(
            pos_fixed=self._trigger_layout
        )
        return FloatLayout.remove_widget(self, widget)


class FixedSimpleMenu(Widget, FixedBase):
    '''
    FixedSimpleMenu is a container to hold a Material-style menu.
    It is expected that clicking on a menu item will either launch
    a FixedPopup to assign a new value.

    Each menu item is a pair of buttons with a transparent background. See
    FixedSimpleMenuItem for details. If true_subheading_font_size or 
    true_font_size are assigned, those values are used as defaults for the
    menu items.

    Sizing Note: to work best with the default font sizing on a 1920x1080 screen,
    each menu item should have a height of 192 each. That allows for 5 menu
    items to fit on a landscape screen. But, in a pinch, 175 seems to work well
    also, which is room for 6.

    This widget, by itself, does not do scrolling.
    '''

    vertical_padding = NumericProperty(0.17)
    background_color = ListProperty([1.0, 1.0, 1.0, 1.0])
    color = ListProperty([0.0, 0.0, 0.0, 1.0])

    def __init__(self, **kwargs):
        self.menu_items = []
        super(FixedSimpleMenu, self).__init__(**kwargs)

    def shape_children(self):
        if self.menu_items:
            item_frame_height = self.size[HEIGHT]/float(len(self.menu_items))
            padding = item_frame_height * self.vertical_padding
            bottom_padding = padding / 2.0
            top_y = (len(self.menu_items) - 1) * item_frame_height
            item_height = item_frame_height - padding
            item_width = self.size[WIDTH] - (padding * 2.0)
            item_x = self.pos[X] + padding
            if self.background_color:
                self.canvas.before.clear()
                with self.canvas.before:
                    Color(*self.background_color)
                    Rectangle(pos=self.pos, size=self.size)
                    middles = len(self.menu_items) - 1
                    if middles>0:
                        Color(0.0, 0.0, 0.0, 0.5)
                        for index in range(middles):
                            line_y = self.pos[Y] + top_y - (index * item_frame_height)
                            Line(points=[self.pos[X], line_y, self.pos[X]+self.size[WIDTH], line_y])
            for index, item in enumerate(self.menu_items):
                item_y = self.pos[Y] + top_y - (index * item_frame_height) + bottom_padding
                item.size = (item_width, item_height)
                item.pos = (item_x, item_y)

    def on_size(self, instance, value):
        self.shape_children()

    def on_pos(self, instance, value):
        self.shape_children()

    def on_parent(self, instance, value):
        self.shape_children()

    def add_widget(self, widget, index=0):
        if isinstance(widget, FixedSimpleMenuItem):
            self.menu_items.append(widget)
            widget.true_subheading_font_size = self.true_subheading_font_size
            widget.true_font_size = self.true_font_size
            widget.color = self.color
            widget.true_scaler = self.true_scaler
        return super(FixedSimpleMenu, self).add_widget(widget, index)

    def set_text(self, child_name, text):
        for child in self.children:
            if child.name == child_name:
                child.text = str(text)
                # child.on_text(child, str(text))

class FixedSimpleMenuItem(Widget, FixedBase):

    heading = StringProperty("Menu item heading")
    text = StringProperty("current value")
    name = StringProperty(None)
    
    def __init__(self, **kwargs):
        self.button_list = []
        self.register_event_type('on_press')
        super(FixedSimpleMenuItem, self).__init__(**kwargs)
        self.heading_button = Button()
        self.heading_button.text = self.heading
        self.heading_button.on_press = self.press_detected
        self.add_widget(self.heading_button)
        self.text_button = Button()
        self.text_button.text = self.text
        self.text_button.on_press = self.press_detected
        self.add_widget(self.text_button)

    def shape_buttons(self):
        half = self.size[HEIGHT] / 2.0
        self.heading_button.pos = (self.pos[X], self.pos[Y]+half)
        self.heading_button.size = (self.size[WIDTH], half)
        self.heading_button.text_size = self.heading_button.size
        self.heading_button.font_size = self.true_scaler(self.true_subheading_font_size)
        self.heading_button.background_color = [0.0, 0.0, 0.0, 0.0]
        self.heading_button.markup = True
        self.heading_button.color = self.color
        self.text_button.pos = (self.pos[X], self.pos[Y])
        self.text_button.size = (self.size[WIDTH], half)
        self.text_button.text_size = self.text_button.size
        self.text_button.font_size = self.true_scaler(self.true_font_size)
        self.text_button.background_color = [0.0, 0.0, 0.0, 0.0]
        self.text_button.color = self.color

    def on_size(self, instance, value):
        self.shape_buttons()

    def on_text(self, instance, value):
        self.text_button.text = value

    def on_heading(self, instance, value):
        self.heading_button.text = "[b]{}[/b]".format(value)

    def on_pos(self, instance, value):
        self.shape_buttons()

    def on_press(self):
        pass

    def press_detected(self):
        self.dispatch('on_press')

class FixedPopup(Widget, FixedBase):
    '''
    FixedPopup

    Don't set pos_fixed. It is used to communicate with FixedLayout.
    Instead, set 'active_pos_fixed' to change it after building.

    To make Floatation work properly, all children are added to the root
    FixedLayout. However, a list of references to children are kept (self.child_references)
    to move the child widgets with the PopUp. This movement only goes "one layer deep".
    '''

    background_color = ListProperty([0.8, 0.8, 0.8, 1.0])
    active_pos_fixed = ListProperty(None)
    off_screen_shift = ListProperty([1920*2, 1920*2])
    active = BooleanProperty(False)

    def __init__(self, *args, **kwargs):
        self.child_references = []
        super(FixedPopup, self).__init__(*args, **kwargs)

    # this is defined to block event propogation to items below the popup
    def on_touch_down(self, touch):
        # if self.active:
        #     if not self.collide_point(*touch.pos):
        #         return True
        if super(FixedPopup, self).on_touch_down(touch):
            return True
        if touch.is_mouse_scrolling:
            return False
        if not self.collide_point(touch.x, touch.y):
            return False
        if self in touch.ud:  # TODO: research what this does
            return False        
        # print "BLOCKED"
        return True

    def _draw_background(self):
        if self.background_color:
            self.canvas.before.clear()
            with self.canvas.before:
                Color(*self.background_color)
                Rectangle(pos=self.pos, size=self.size)

    def _shift(self, my_pos):
        x = my_pos[X] + self.off_screen_shift[X]
        y = my_pos[Y] + self.off_screen_shift[Y]
        return (x, y)

    def _placement(self):
        if not self.active_pos_fixed:
            return
        if self.active:
            self.pos_fixed = self.active_pos_fixed
            for c in self.child_references:
                if c.active_pos_fixed:
                    c.pos_fixed = c.active_pos_fixed
        else:
            self.pos_fixed = self._shift(self.active_pos_fixed)
            for c in self.child_references:
                if c.active_pos_fixed:
                    c.pos_fixed = self._shift(c.active_pos_fixed)

    def on_size(self, instance, value):
        self._draw_background()
        self._placement()

    def on_pos(self, instance, value):
        self._draw_background()
        self._placement()

    def on_active(self, instance, value):
        self._draw_background()
        self._placement()

    def add_widget(self, widget):
        self.add_to_root(widget)
        self.child_references.append(widget)

    def remove_widget(self, widget):
        self.delete_from_root(widget)
        self.child_references.append(widget)

    # def add_widget(self, widget, index=0):
    #     return super(FixedPopup, self).add_widget(widget, index)

    # def remove_widget(self, widget):
    #     widget.unbind(
    #         active_pos_fixed=self.handle_child_pos_fixed
    #     )
    #     return super(FixedPopup, self).add_widget(widget, index)


class FixedRadioButtons(Widget, FixedBase):
    
    selections = ListProperty([])
    color = ListProperty([1, 1, 1, 1])
    selected = NumericProperty(0)
    background_normal = StringProperty(None)
    background_selected = StringProperty(None)
    layout = StringProperty("vertical")
    separation_factor = NumericProperty(1.0)
    # on_selection = ObjectProperty(None)

    def __init__(self, **kwargs):
        self.label_list = []
        self.selector_list = []
        self.label_y_shift = 150
        self.label_y_incr = 100
        self.label_x_shift = 150
        self.label_x_incr = 100
        self.register_event_type('on_selection')
        super(FixedRadioButtons, self).__init__(**kwargs)

    def on_color(self, instance, value):
        for index, label in enumerate(self.label_list):
            label.color = value

    def _calc_button_pos(self, my_pos, index):
        if self.layout=="horizontal":
            x = my_pos[X] + (index * self.label_x_incr) + self.label_x_shift
            y = my_pos[Y]
        else:
            top_y = len(self.selections) * self.label_y_incr - self.label_y_incr
            x = my_pos[X] + self.label_x_shift
            y = my_pos[Y] + top_y - (index * self.label_y_incr)
        return (x, y)

    def _calc_button_size(self):
        if self.layout=="horizontal":
            width = self.label_x_incr - self.label_x_shift
            height = self.size[Y]
        else:
            width = self.size[X] - self.label_x_shift
            if width < 0:
                width = 100
            height = self.label_y_incr
        return (width, height)

    def _calc_sel_pos(self, my_pos, index):
        if self.layout=="horizontal":
            x = my_pos[X] + (index * self.label_x_incr)
            y = my_pos[Y]
        else:
            top_y = len(self.selections) * self.label_y_incr - self.label_y_incr
            x = my_pos[X]
            y = my_pos[Y] + top_y - (index * self.label_y_incr)
        return (x, y)

    def _calc_sel_size(self):
        if self.layout=="horizontal":
            width = self.size[HEIGHT]
            height = self.size[HEIGHT]
        else:
            width = self.label_y_incr
            height = self.label_y_incr
        return (width, height)

    def _recalc_shifts(self):
        if self.label_list:
            self.label_y_incr = self.size[HEIGHT] / float(len(self.label_list))
            self.label_x_incr = self.size[WIDTH] / float(len(self.label_list))
            if self.layout=="horizontal":
                self.label_x_shift = self.size[HEIGHT] * self.separation_factor
            else:
                self.label_x_shift = self.label_y_incr * self.separation_factor

    def on_pos(self, instance, value):
        self._recalc_shifts()
        for index, label in enumerate(self.label_list):
            label.pos = self._calc_button_pos(value, index)
            label.size = self._calc_button_size()
            self.selector_list[index].pos = self._calc_sel_pos(value, index)
            self.selector_list[index].size = self._calc_sel_size()

    def on_size(self, instance, value):
        self._recalc_shifts()
        for index, label in enumerate(self.label_list):
            label.size = self._calc_button_size()
            label.text_size = label.size
            if self.true_font_size:
                label.font_size = self.parent.true_scaler(self.true_font_size)
            self.selector_list[index].size = self._calc_sel_size()

    def on_separation_factor(self, instance, value):
        return self.on_pos(instance, value)

    def selection_made(self, instance):
        index = instance.selected_number
        if index==self.selected:
            return
        self.selector_list[self.selected].text = "O"
        self.selected = index
        self.selector_list[self.selected].text = "X"
        if self.on_selection:
            self.dispatch('on_selection')

    def on_selection(self):
        pass

    def on_selections(self, instance, value_list):
        # FAIR WARNING: Do not confuse this with 'on_selection'
        # first, check to see if changed
        same = True
        for index, text in enumerate(value_list):
            if text != grab(self.label_list, index):
                same = False
        if same:
            return
        self.clear_widgets()
        self.label_list = []
        self.selector_list = []
        self._recalc_shifts()
        for index, text in enumerate(value_list):
            new_label = Button(text=str(text))
            new_label.pos = self._calc_button_pos(self.pos, index)
            new_label.color = self.color
            new_label.size = self._calc_button_size()
            new_label.halign = 'left'
            new_label.valign = 'middle'
            new_label.background_color = (0, 0, 0, 0)
            new_label.selected_number = index
            new_label.role = "label"
            new_label.bind(on_press=self.selection_made)
            self.add_widget(new_label)
            self.label_list.append(new_label)
            new_sel = Button()
            new_sel.pos = self._calc_sel_pos(self.pos, index)
            new_sel.color = self.color
            new_sel.size = self._calc_sel_size()
            new_sel.selected_number = index
            new_sel.role = "selector"
            new_sel.bind(on_press = self.selection_made)
            self.add_widget(new_sel)
            self.selector_list.append(new_sel)
        self._update_selected(self.selected)

    def _update_selected(self, index):
        for s in self.selector_list:
            pass
            # TODO: restore
            # if s.selected_number==index:
            #     s.background_normal = self.background_selected
            # else:
            #     s.background_normal = self.background_normal
            
    def on_selected(self, instance, index):
        self._update_selected(index)

    def on_background_normal(self, instance, value):
        self._update_selected(self.selected)

    def on_background_selected(self, instance, value):
        self._update_selected(self.selected)


    # def add_widget(self, widget, index=0):
    #     #widget.size = (1920, 1080)
    #     widget.bind(
    #        pos_hint=self.parent._trigger_layout
    #     )
    #     return super(FixedSelector, self).add_widget(widget, index)

    # def remove_widget(self, widget):
    #     widget.unbind(
    #         pos_hint=self.parent._trigger_layout
    #     )
    #     return super(FixedSelector, self).remove_widget(widget)

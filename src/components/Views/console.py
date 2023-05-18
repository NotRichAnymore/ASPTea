import logging
import sys
import traceback
import pysnooper
import PySimpleGUI as sg
from src.components.Views import settingsWindow, mainWindow
from src.data.files.custom_themes import custom_themes
from src.components.Utilities.loggingUtilities import LoggingUtilities
from pathlib import Path


class Console:

    def __init__(self, command_controller, window_controller, settings_controller, logger):
        self.save_folder = None
        self.command_controller = command_controller
        self.window_controller = window_controller
        self.settings_controller = settings_controller
        self.theme = None
        self.settings = None
        self.themes = None
        self.custom_themes = custom_themes
        self.main_window_keys = None
        self.suffix = None
        self.main_window_num = 0
        self.settings_window_num = 0
        self.preview_theme_window_num = 0
        self.logger = logger

    def initialise_themes(self):
        self.logger.create_log_entry(level=logging.CRITICAL, message='Initialising Themes')
        for name, theme in zip(self.custom_themes.keys(), self.custom_themes.values()):
            sg.theme_add_new(name, theme)
            self.logger.create_log_entry(level=logging.DEBUG, message=f'Adding Theme: {name}')
        self.logger.create_log_entry(level=logging.CRITICAL, message='Themes set')

    @pysnooper.snoop()
    def load_settings(self, default_path=False, path=None):
        self.logger.create_log_entry(level=logging.CRITICAL, message='Loading Settings')
        self.settings = self.settings_controller.load_settings(default_path, path)
        self.logger.create_log_entry(level=logging.CRITICAL, message='Settings loaded')

    def establish_current_theme(self, theme=None):
        # If a theme has been chosen update current and previous theme
        # Send the current theme for updating
        # Change the current one, only if a new theme has been chosen
        if theme:
            self.logger.create_log_entry(level=logging.CRITICAL, message='Setting New Theme')
            new_theme = self.settings_controller.manage_theme(theme)
            self.theme = new_theme
        # otherwise return the current theme
        self.logger.create_log_entry(level=logging.CRITICAL, message='Getting Current Theme')
        return self.theme

    @pysnooper.snoop()
    def establish_save_folder(self, save_folder=None):
        if save_folder:
            updated_settings = self.settings_controller.manage_save_folder(save_folder)
            self.logger.create_log_entry(level=logging.CRITICAL, message='Save Folder Updated')
            self.save_folder = updated_settings['Files']['save_folder']
            self.settings = updated_settings
            self.logger.create_log_entry(level=logging.CRITICAL, message='Settings Updated')

    def establish_user_variables(self, username, password):
        self.logger.create_log_entry(level=logging.CRITICAL, message=f'Setting User Details')
        success = self.settings_controller.set_credentials(username, password)
        self.logger.create_log_entry(level=logging.CRITICAL, message=f'User Details created: {success}')

    def execute_command(self, command_arguments):
        command = self.command_controller.load_command(command_arguments)
        # (command)
        return self.command_controller.run_command(command)

    def get_active_window(self):
        self.logger.create_log_entry(level=logging.CRITICAL, message='Getting active window')
        return self.window_controller.get_active_window()

    def update_active_window(self, window_to_close, active_window, program_running=None):
        self.logger.create_log_entry(level=logging.CRITICAL, message='Updating active window')
        self.window_controller.update_active_window_(window_to_close, active_window, program_running)

    @staticmethod
    def end_program(main_window):
        main_window.close()
        del [main_window]

    def program_setup(self):
        self.logger.start_logger()
        self.logger.create_log_entry(level=logging.CRITICAL, message='Starting Program Setup')
        self.load_settings(default_path=True)
        self.initialise_themes()
        settings = self.settings
        current_theme_from_file = settings['System']['current_theme']
        self.establish_current_theme(current_theme_from_file)
        # Set main window as the currently running window and gui is currently running
        self.update_active_window(None, 'main_window', True)
        self.logger.create_log_entry(level=logging.CRITICAL, message='Ending Program Setup')


    @pysnooper.snoop()
    def run_settings_window(self):
        settings = self.settings
        settings_window_ = settingsWindow.SettingsWindow()
        window = settings_window_.create_new_window(window_num=str(self.settings_window_num))
        # Until the settings window isn't the active window
        active_window = self.get_active_window()
        try:
            while active_window == 'settings_window':
                event, values = window.read()
                print(event, values)
                sg.theme(self.establish_current_theme())
                self.suffix = "_" + str(self.settings_window_num)
                # if the exit button is pressed on the settings menu
                if event == f'settings_window_exit_button{self.suffix}':
                    # update the active window manager for the settings window to be closing
                    self.update_active_window('settings_window', 'main_window', True)
                    if self.get_active_window() != 'settings_window':
                        window.close()
                        break

                elif event == f'program_theme_button{self.suffix}':
                    updated_theme = settings_window_.run_preview_themes_window(self.preview_theme_window_num,
                                                                               self.establish_current_theme())
                    self.establish_current_theme(updated_theme)
                    self.settings_window_num += 1
                    window.close()
                    window = settings_window_.create_new_window(window_num=str(self.settings_window_num),
                                                                new_theme=self.establish_current_theme())

                elif event == f'load_save_folder_button{self.suffix}':
                    success = True
                    save_folder = values[f'save_folder_input{self.suffix}']
                    self.establish_save_folder(save_folder)
                    if self.save_folder is None or self.save_folder == save_folder:
                        success = False
                    sg.popup_timed(f'Save Folder Changed: {success}?', keep_on_top=True)

                elif event == f'select_folder_button{self.suffix}':
                    save_folder = settings_window_.run_select_folder_window()
                    self.establish_save_folder(save_folder)
                    window[f'save_folder_input{self.suffix}'].update(self.save_folder)

                elif event == f'set_user_button{self.suffix}':
                    username = values[f'username_input{self.suffix}']
                    password = values[f'password_input{self.suffix}']
                    self.establish_user_variables(username, password)

                elif event == f'load_user_button{self.suffix}':
                    pass

        except Exception as e:
            window.close()
            del[window]

    @pysnooper.snoop()
    def run(self):
        # Setup Program
        self.program_setup()
        reload_contents = False
        reload_window = False

        # Setup Window variables
        main_window = mainWindow.MainWindow()
        sg.theme(self.establish_current_theme())
        window = main_window.run_window()
        main_loop = True
        while main_loop:
            try:
                if reload_window:
                    self.main_window_num += 1
                    self.logger.create_log_entry(level=logging.DEBUG, message='Creating New Window')
                    window = main_window.create_new_window(window_num=str(self.main_window_num),
                                                           new_theme=self.establish_current_theme())
                    reload_window = False
                    
                self.suffix = "_" + str(self.main_window_num)

                if not main_loop:
                    self.logger.create_log_entry(level=logging.ERROR, message='Closing Program')
                    break

                run_event_loop = True
                while run_event_loop:
                    if self.main_window_num > 0 and reload_contents:
                        for line in self.window_controller.load_console_output():
                            print(line.rstrip())
                        reload_contents = False

                    event, values = window.read()
                    # If Exit button is pressed on the main menu
                    if event == f'main_window_exit_button{self.suffix}':
                        #  update the active window manager
                        self.update_active_window('main_window', None, False)
                        # close and destroy the window
                        self.end_program(window)
                        # exit the loop
                        run_event_loop = False
                        main_loop = False

                    # If the settings button is pressed on the main menu
                    elif event == f'main_window_settings_button{self.suffix}':
                        # update the active window manager for the settings window to be currently running
                        self.update_active_window('main_window', 'settings_window', True)
                        # save the console for reloading, run settings
                        # regardless of the output, reload console
                        if self.get_active_window() == 'settings_window':
                            self.window_controller.save_console_output(self.settings, values[f'output_screen{self.suffix}'])
                            window.close()
                            self.run_settings_window()
                            reload_contents = True
                            reload_window = True
                            run_event_loop = False

                    elif event == f'load_input_button{self.suffix}':
                        command_arguments = values[f'command_arguments{self.suffix}']
                        print(command_arguments)
                        print(self.execute_command(command_arguments))

                    if not run_event_loop:
                        break



            except Exception as e:
                sg.popup_error(e.with_traceback(traceback.print_exc(file=sys.stdout)),
                               auto_close=True, auto_close_duration=0.01)
                continue
                # sg.popup_error(e.with_traceback(traceback.print_exc(file=sys.stdout)), keep_on_top=True)
                # self.settings_controller.get_previous_theme()
                #     if self.theme is None else self.settings_controller.get_current_theme()

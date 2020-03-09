import os
import ctypes
import logging
import shutil

from subprocess import check_output
from mu.modes.base import MicroPythonMode, FileManagerOs
from mu.modes.api import MEOWBIT_APIS, SHARED_APIS
from mu.interface.panes import CHARTS
from mu.resources import load_icon
from mu.contrib import pybfs
from PyQt5.QtCore import QThread

logger = logging.getLogger(__name__)

class MeowbitMode(MicroPythonMode):
    """
    Meowbit main class entry
    """
    name = _('Meowbit Micropython')
    description = _('Micropython support for kittenbot meowbit')
    icon = 'meowbit'
    save_timeout = 0
    valid_boards = (
        (0xF055, 0x9800),  # pyboard
    )

    def actions(self):
        buttons = [
            {
                'name': 'run',
                'display_name': _('Run'),
                'description': _('Run the code'),
                'handler': self.run_script,
                'shortcut': 'F5',
            },
            {
                'name': 'repl',
                'display_name': _('REPL'),
                'description': _('Use the REPL to live-code on the '
                                 'micro:bit.'),
                'handler': self.toggle_repl,
                'shortcut': 'Ctrl+Shift+I',
            },
            {
                'name': 'files',
                'display_name': _('Files'),
                'description': _('Access the file system on the micro:bit.'),
                'handler': self.toggle_files,
                'shortcut': 'F4',
            }
        ]
        if CHARTS:
            buttons.append({
                'name': 'plotter',
                'display_name': _('Plotter'),
                'description': _('Plot incoming REPL data.'),
                'handler': self.toggle_plotter,
                'shortcut': 'CTRL+Shift+P',
            })
        return buttons

    def run_toggle(self):
        """
        Handles the toggling of the run button to start/stop a script.
        """


    def run_script(self):
        """
        copy file to flash device and try execute
        """
        # Grab the Python file.
        tab = self.view.current_tab
        serial = self.editor._view.serial
        data_received = self.editor._view.data_received
        if serial:
            serial.close()

        print(serial, data_received)
        if tab is None:
            print('No active script')
            self.stop_script()
            return
        if tab.path is None:
            # Unsaved file.
            self.editor.save()
        if tab.path:
            script = tab.text()
            try:
                serial = pybfs.get_serial()
                out, err = pybfs.execute([script], serial)
                serial.close()
                print('RET', out, err)
                data_received.emit(out)
            except Exception as e:
                print('Err {}'.format(e))
            self.editor._view.reopen_serial_link()

    def toggle_repl(self, event):
        """
        Check for the existence of the file pane before toggling REPL.
        """
        super().toggle_repl(event)
        if self.repl:
            self.set_buttons(flash=False, files=False)
        elif not (self.repl or self.plotter):
            self.set_buttons(flash=True, files=True)

    def toggle_files(self, event):
        """
        Check for the existence of the REPL or plotter before toggling the file
        system navigator for the MicroPython device on or off.
        """
        if self.fs is None:
            self.add_fs()
            if self.fs:
                logger.info('Toggle filesystem on.')
                self.set_buttons(run=False, repl=False, plotter=False)
        else:
            self.remove_fs()
            logger.info('Toggle filesystem off.')
            self.set_buttons(run=True, repl=True, plotter=True)


    def toggle_plotter(self, event):
        """
        Check for the existence of the file pane before toggling plotter.
        """
        super().toggle_plotter(event)
        if self.plotter:
            self.set_buttons(flash=False, files=False)
        elif not (self.repl or self.plotter):
            self.set_buttons(flash=True, files=True)

    def find_workspace(self):
        """
        Return the default location on the filesystem for opening and closing
        files.
        """
        def get_volume_size(disk_name):
            total, used, free = shutil.disk_usage(disk_name)
            # print(disk_name, total, used, free)
            return total
        def get_volume_name(disk_name):
            """
            Each disk or external device connected to windows has an
            attribute called "volume name". This function returns the
            volume name for the given disk/device.

            Code from http://stackoverflow.com/a/12056414
            """
            vol_name_buf = ctypes.create_unicode_buffer(1024)
            ctypes.windll.kernel32.GetVolumeInformationW(
                ctypes.c_wchar_p(disk_name), vol_name_buf,
                ctypes.sizeof(vol_name_buf), None, None, None, None, 0)
            return vol_name_buf.value
        device_dir = None
        # Attempts to find the path on the filesystem that represents the
        # plugged in CIRCUITPY board.
        if os.name == 'posix':
            # We're on Linux or OSX
            for mount_command in ['mount', '/sbin/mount']:
                try:
                    mount_output = check_output(mount_command).splitlines()
                    mounted_volumes = [x.split()[2] for x in mount_output]
                    for volume in mounted_volumes:
                        if volume.endswith(b'MEOWBIT'):
                            device_dir = volume.decode('utf-8')
                except FileNotFoundError:
                    next
        elif os.name == 'nt':
            #
            # In certain circumstances, volumes are allocated to USB
            # storage devices which cause a Windows popup to raise if their
            # volume contains no media. Wrapping the check in SetErrorMode
            # with SEM_FAILCRITICALERRORS (1) prevents this popup.
            #
            old_mode = ctypes.windll.kernel32.SetErrorMode(1)
            try:
                pathList = []
                for disk in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                    path = '{}:\\'.format(disk)
                    if os.path.exists(path):
                        pathList.append(path)
                        if get_volume_size(path) < 16777216:
                            return path
                        elif get_volume_name(path) == 'MEOWBIT':
                            return path
            finally:
                ctypes.windll.kernel32.SetErrorMode(old_mode)
        else:
            # No support for unknown operating systems.
            raise NotImplementedError('OS "{}" not supported.'.format(os.name))

    def add_fs(self):
        """
        Add the file system navigator to the UI.
        """
        # Find serial port the ESP8266/ESP32 is connected to
        device_port, serial_number = self.find_device()
        workspace = self.find_workspace()
        
        self.file_manager_thread = QThread(self)
        self.file_manager = FileManagerOs(device_port, workspace)
        self.file_manager.moveToThread(self.file_manager_thread)
        self.file_manager_thread.started.\
            connect(self.file_manager.on_start)
        self.fs = self.view.add_filesystem(self.workspace_dir(),
                                           self.file_manager,
                                           _("Meowbit"))
        self.fs.set_message.connect(self.editor.show_status_message)
        self.fs.set_warning.connect(self.view.show_message)
        self.file_manager_thread.start()


    def remove_fs(self):
        self.view.remove_filesystem()
        self.file_manager = None
        self.file_manager_thread = None
        self.fs = None

    def api(self):
        """
        Return a list of API specifications to be used by auto-suggest and call
        tips.
        """
        return SHARED_APIS + MEOWBIT_APIS






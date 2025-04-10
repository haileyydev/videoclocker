import sys
import argparse
import gi
import subprocess
from gi.repository import GLib
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from pynvml import *

nvmlInit()
myGPU = nvmlDeviceGetHandleByIndex(0)

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_default_size(600, 0)
        self.set_title(f"Videoclocker: GPU 0 - {nvmlDeviceGetName(myGPU)}")

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)

        gpu_frame = Gtk.Frame(label="GPU Info")
        gpu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.gpulabel = Gtk.Label(label=f"GPU: {nvmlDeviceGetName(myGPU)}")
        self.gpuclocklabel = Gtk.Label(label=f"Video Clock Speed: {nvmlDeviceGetClockInfo(myGPU, NVML_CLOCK_GRAPHICS)} MHz")
        self.memclocklabel = Gtk.Label(label=f"Memory Clock Speed: {nvmlDeviceGetClockInfo(myGPU, NVML_CLOCK_MEM)} MHz")
        self.memclocklabel.set_margin_bottom(10)
        gpu_box.append(self.gpulabel)
        gpu_box.append(self.gpuclocklabel)
        gpu_box.append(self.memclocklabel)
        gpu_frame.set_child(gpu_box)
        main_box.append(gpu_frame)

        boost_frame = Gtk.Frame(label="Overclock Settings")
        boost_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        boost_box.append(Gtk.Label(label="Video Clock Boost (MHz)"))
        self.gpuslider = Gtk.Scale()
        self.gpuslider.set_range(-500, 500)
        self.gpuslider.set_value(0)
        self.gpuslider.set_digits(0)
        self.gpuslider.set_draw_value(True)
        boost_box.append(self.gpuslider)

        boost_box.append(Gtk.Label(label="Memory Clock Boost (MHz)"))
        self.memslider = Gtk.Scale()
        self.memslider.set_range(-2000, 5000)
        self.memslider.set_value(0)
        self.memslider.set_digits(0)
        self.memslider.set_draw_value(True)
        boost_box.append(self.memslider)

        turbo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        turbo_box.set_halign(Gtk.Align.CENTER)

        self.super_turbo_checkbox = Gtk.CheckButton()
        turbo_box.append(self.super_turbo_checkbox)
        turbo_box.append(Gtk.Label(label="Turbo Mode"))

        boost_box.append(turbo_box)

        self.super_turbo_label = Gtk.Label(label="Turbo Mode locks your GPU's clock frequencies to the max at all times")
        self.super_turbo_label.set_margin_bottom(10)
        boost_box.append(self.super_turbo_label)

        boost_frame.set_child(boost_box)
        main_box.append(boost_frame)

        power_frame = Gtk.Frame(label="Power Settings")
        power_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        power_box.append(Gtk.Label(label="Power Limit (W)"))
        self.powerslider = Gtk.Scale()
        self.powerslider.set_range(nvmlDeviceGetPowerManagementLimitConstraints(myGPU)[0]/1000, nvmlDeviceGetPowerManagementLimitConstraints(myGPU)[1]/1000)
        self.powerslider.set_value(nvmlDeviceGetPowerManagementDefaultLimit(myGPU)/1000)
        self.powerslider.set_digits(0)
        self.powerslider.set_draw_value(True)
        power_box.append(self.powerslider)

        power_frame.set_child(power_box)
        main_box.append(power_frame)

        self.apply_button = Gtk.Button(label="Apply")
        self.apply_button.set_margin_top(10)
        self.apply_button.connect("clicked", self.on_apply_clicked)
        main_box.append(self.apply_button)

        self.set_child(main_box)
        GLib.timeout_add(GLib.PRIORITY_DEFAULT, 1000, self.update_info)

    def update_info(self):
        self.gpuclocklabel.set_label(f"Video Clock Speed: {nvmlDeviceGetClockInfo(myGPU, NVML_CLOCK_GRAPHICS)} MHz")
        self.memclocklabel.set_label(f"Memory Clock Speed: {nvmlDeviceGetClockInfo(myGPU, NVML_CLOCK_MEM)} MHz")
        return True

    def on_apply_clicked(self, button):
        gpu_boost = int(self.gpuslider.get_value())
        mem_boost = int(self.memslider.get_value())
        power_limit = int(self.powerslider.get_value())
        turbo_on = self.super_turbo_checkbox.get_active()
        if turbo_on == True:
            turbo_on = 1
        else:
            turbo_on = 0
        subprocess.run(["pkexec", sys.executable, "--gpuboost", str(gpu_boost), "--memboost", str(mem_boost), "--turbo", str(turbo_on), "--power", str(power_limit), "--quit", "1"])

class MyApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.win = MainWindow(application=app)
        self.win.present()

parser = argparse.ArgumentParser()
parser.add_argument('--gpuboost', type=int, help='gpu boost clock (mhz)')
parser.add_argument('--memboost', type=int, help='mem boost clock (mhz)')
parser.add_argument('--turbo', type=int, help='turbo mode (0 or 1)')
parser.add_argument('--power', type=int, help='power limit (watts)')
parser.add_argument('--quit', type=int, help='quit')

args = parser.parse_args()

if args.gpuboost is not None:
    nvmlDeviceSetGpcClkVfOffset(myGPU, args.gpuboost)
if args.memboost is not None:
    nvmlDeviceSetMemClkVfOffset(myGPU, args.memboost*2)
if args.power is not None:
    nvmlDeviceSetPowerManagementLimit(myGPU, args.power*1000)
if args.turbo is not None:
    if args.turbo == 0:
        nvmlDeviceSetMemoryLockedClocks(myGPU, 0, 0)
        nvmlDeviceSetGpuLockedClocks(myGPU, 0, 0)
    else:
        nvmlDeviceSetMemoryLockedClocks(myGPU, 100000, 100000)
        nvmlDeviceSetGpuLockedClocks(myGPU, 100000, 100000)

if args.quit is not None:
    exit()

app = MyApp(application_id="dev.haileyy.videoclocker")
app.run(sys.argv)

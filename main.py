import time
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.clock import Clock
from jnius import autoclass

# Java classes for Bluetooth
BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
BluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')
UUID = autoclass('java.util.UUID')


class MyGridLayout(GridLayout):
    def __init__(self, **kwargs):
        super(MyGridLayout, self).__init__(**kwargs)
        self.cols = 1

        # Top Grid for Input
        self.top_grid = GridLayout()
        self.top_grid.cols = 2
        self.top_grid.add_widget(Label(text="Select Device: "))
        self.name = TextInput(multiline=False)
        self.top_grid.add_widget(self.name)
        self.add_widget(self.top_grid)

        # Connect Button
        self.submit = Button(text="Connect", font_size=32)
        self.submit.bind(on_press=self.connect_to_device)
        self.add_widget(self.submit)

        # Status Label
        self.status_label = Label(text="Status: Not Connected")
        self.add_widget(self.status_label)

        # Initialize Bluetooth Adapter and Socket
        self.adapter = BluetoothAdapter.getDefaultAdapter()
        self.socket = None

        # Get Paired Devices
        self.devices = {}
        self.get_paired_devices()

    def get_paired_devices(self):
        """Fetch paired Bluetooth devices."""
        if not self.adapter:
            self.status_label.text = "Bluetooth Not Supported"
            return

        paired_devices = self.adapter.getBondedDevices().toArray()
        self.devices = {device.getName(): device for device in paired_devices}

        if not self.devices:
            self.status_label.text = "No paired devices found."
        else:
            self.status_label.text = "Devices Found: " + ", ".join(self.devices.keys())

    def connect_to_device(self, instance):
        """Initiate Bluetooth connection."""
        device_name = self.name.text.strip()
        if not device_name or device_name not in self.devices:
            self.status_label.text = "Invalid Device Name"
            return

        self.status_label.text = "Connecting..."
        self.device = self.devices[device_name]

        # Standard UUID for serial communication (SPP)
        self.uuid = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")

        # Use Clock.schedule_once to manage connection steps
        self.connection_attempts = 0
        Clock.schedule_once(self.try_connect)

    def try_connect(self, dt):
        """Try to connect to the selected Bluetooth device in steps."""
        try:
            # Step 1: Create the socket (if not already created)
            if self.socket is None:
                self.socket = self.device.createRfcommSocketToServiceRecord(self.uuid)
                self.status_label.text = "Socket Created"

            # Step 2: Attempt to connect
            if not self.socket.isConnected():
                self.socket.connect()
                self.status_label.text = "Connected Successfully!"
                Clock.schedule_interval(self.send_data, 0.5)  # Start sending data every 500ms
            else:
                self.status_label.text = "Already Connected"
        except Exception as e:
            self.connection_attempts += 1
            if self.connection_attempts < 3:  # Retry up to 3 times
                self.status_label.text = f"Retrying Connection ({self.connection_attempts})..."
                Clock.schedule_once(self.try_connect, 1)  # Retry after 1 second
            else:
                self.status_label.text = f"Connection Failed: {e}"
                self.socket = None  # Reset socket for future attempts

    def send_data(self, dt):
        """Send data to the connected device."""
        try:
            if self.socket and self.socket.isConnected():
                message = "Hello World\n"
                self.socket.getOutputStream().write(message.encode('utf-8'))
                self.socket.getOutputStream().flush()
                self.status_label.text = "Data Sent"
            else:
                self.status_label.text = "Socket Disconnected"
                Clock.unschedule(self.send_data)
        except Exception as e:
            self.status_label.text = f"Send Failed: {e}"
            Clock.unschedule(self.send_data)

    def on_stop(self):
        """Clean up resources on app stop."""
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                print(f"Error closing socket: {e}")


class MyApp(App):
    def build(self):
        return MyGridLayout()


if __name__ == '__main__':
    MyApp().run()

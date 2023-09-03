#MIT License

#Copyright (c) [2023] [Trevor Beaton]

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

import time
import board
import displayio
import framebufferio
import rgbmatrix
import terminalio
from adafruit_display_text import label
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

SEND_RATE = 10  # how often in seconds to send text

count = 0

SCROLL_DELAY = 0.05  # delay between scrolls, in seconds

ble = BLERadio()
uart_server = UARTService()
advertisement = ProvideServicesAdvertisement(uart_server)

# Release any previously allocated displays
displayio.release_displays()

matrix = rgbmatrix.RGBMatrix(
    width=64, height=32, bit_depth=1,
    rgb_pins=[board.D6, board.A5, board.A1, board.A0, board.A4, board.D11],
    addr_pins=[board.D10, board.D5, board.D13, board.D9],
    clock_pin=board.D12, latch_pin=board.RX, output_enable_pin=board.TX,
)
display = framebufferio.FramebufferDisplay(matrix, auto_refresh=True)

main_group = displayio.Group()

def scroll(line):
    line.x -= 1
    line_width = line.bounding_box[2]
    if line.x < -line_width:
        line.x = display.width

def update_display(text, color=0xFFFFFF):
    """Update the display with the provided text and color."""
    if len(main_group) > 0:
        main_group.pop()
    text_area = label.Label(terminalio.FONT, text=text, color=color)
    text_area.x = display.width
    text_area.y = 13
    main_group.append(text_area)
    display.show(main_group)

while True:
    print("WAITING...")
    update_display("WAITING...")
    ble.start_advertising(advertisement)

    while not ble.connected:
        scroll(main_group[0])
        display.refresh(minimum_frames_per_second=0)
        time.sleep(SCROLL_DELAY)

    # Connected
    ble.stop_advertising()
    print("CONNECTED")
    update_display("CONNECTED")

    # Loop and read packets
    last_send = time.monotonic()
    while ble.connected:
        if uart_server.in_waiting:
            raw_bytes = uart_server.read(uart_server.in_waiting)
            text = raw_bytes.decode().strip()
            print("RX:", text)
            update_display(text, color=0x26B7FF)

        if time.monotonic() - last_send > SEND_RATE:
            text = "COUNT = {}".format(count)
            print("TX:", text)
            uart_server.write((text + "\r\n").encode())
            count += 1
            last_send = time.monotonic()

        scroll(main_group[0])
        display.refresh(minimum_frames_per_second=0)
        time.sleep(SCROLL_DELAY)

    print("DISCONNECTED")

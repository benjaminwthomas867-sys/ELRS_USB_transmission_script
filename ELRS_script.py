import time
import serial

SERIAL_PORT = "COM3" #change to the COM port of your attached USB transitter. This can be found in Device manager > Ports(COM & LPT)
BAUD_RATE = 420000  # crsf baud rate

#crsf constants
crsf_sync = 0xC8
crsf_frametype = 0x16

def calc_crc_checksum(data): # produces the crc checksum
  crc = 0
  for byte in data:
    crc ^= byte
    for _ in range(8):
      if crc & 0x80:
        crc = ((crc << 1) ^ 0xD5) & 0xFF
      else:
        crc = (crc << 1) & 0xFF
  return crc

def create_rc_channels_frame(channels):
  data = 0
  bits_filled = 0
  payload_bits = []

  for channel in channels:
    #ensures the value is between 1811 and 172
    val = max(172, min(1811, channel))
    data |= val << bits_filled
    bits_filled += 11
    while bits_filled >= 8:
      payload_bits.append(data & 0xFF)
      data >>= 8
      bits_filled -= 8

  if bits_filled > 0:
    payload_bits.append(data & 0xFF)
  payload = bytes(payload_bits[:22])

  # structure: type, payload
  frame_data = bytes([crsf_frametype]) + payload
  checksum = calc_crc_checksum(frame_data)
  length = len(frame_data) + 1
  frame = bytes([crsf_sync, length]) + frame_data + bytes([checksum])

  return frame

try:
  ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
  print(f"Connected to ELRS USB module on {SERIAL_PORT} at {BAUD_RATE} baud.")
  
    # roll, pitch, throttle, yaw, aux1, aux2 ...
    #992 is the 'neutral position' on a drone controller. 172 is the lowest value. throttle is set by default to 172.
  channels = [992, 992, 172, 992, 172, 992, 992, 992] + [992] * 8

  while True:
    channel_input = int(input("input the channel you want to change")) # input the channel number you want to change from the above array
    new_value = int(input("input the new value 172<value<1811")) #input the new value you want
    channels[channel_input] = new_value 
    frame = create_rc_channels_frame(channels)
    ser.write(frame)
    time.sleep(0.006667)  # sends at a frequency of 150hz

except serial.SerialException as e:
  print(f"serial communication error {e}") # catches and prints any errors in communications

finally:
  if "ser" in locals() and ser.is_open:
    ser.close() 

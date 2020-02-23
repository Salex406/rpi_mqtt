#sudo apt-get install -y i2c-tools
#sudo i2cdetect -y 1
#sudo nano /boot/config.txt

from smbus import SMBus
import fcntl
import time


l_addr = 0x23
temp_cmd = 0xF3
hum_cmd = 0xF5
channel = 1

bus = SMBus(1)
bus.write_byte(l_addr, 0x01)
time.sleep(0.5)
bus.write_byte(l_addr, 0x47)
time.sleep(0.5)
bus.write_byte(l_addr, 0x7F)
time.sleep(0.5)
bus.write_byte(l_addr, 0x11)
#T = bus.read_i2c_block_data(sht_addr, 0x03, 3)
time.sleep(0.5)
temp_h = bus.read_byte(l_addr)
temp_l = bus.read_byte(l_addr)
res = ((temp_h<<8)|temp_l)/1.2

print(res)

"""
Драйвер для nrf, принимающий и обрабатвающий посылки(сейчас только протечки)
затем запускается notify_sender или tb(отключен)
Активаия по isActivated
"""

import subprocess
import sys
import os
import datetime
from subprocess import Popen, PIPE, run

import spidev
import time
import RPi.GPIO as GPIO

#IRQ GPIO15
#SPI0
#CS GPIO24
#CE GPIO26

motion_id = '/home/pi/alert_state/m_on'

#activation check
isActivated_file = '/home/pi/SmartHome/isActivated'
logEnabled_file = '/home/pi/SmartHome/logEnabled'

with open(isActivated_file) as afile_handler:
	ActivationStatus = afile_handler.read(1)
	ActStatus = bool(int(ActivationStatus))
	
while(not ActStatus):
	time.sleep(10)
	with open(isActivated_file) as afile_handler:
		ActivationStatus = afile_handler.read(1)
		ActStatus = bool(int(ActivationStatus))

#log check
with open(logEnabled_file) as lfile_handler:
		LogStatus = lfile_handler.read(1)
		LStatus = bool(int(LogStatus))

WRITE_MASK = 0x20 #001_5bitOFReg
READ_MASK = 0x00 #000_5bitOFReg
W_PAYLOAD = 0xA0
R_PAYLOAD = 0x61
R_RX_PL_WID = 0x60
FLUSH_TX = 0xE1
FLUSH_RX = 0xE2
NOP = 0xFF
IRQ_PIN = 15
CS_PIN = 24
CE_PIN = 26

CONFIG = 0x00
EN_AA = 0x01
EN_RXADDR = 0x02
SETUP_AW = 0x03
RF_CH = 0x05
RF_SETUP = 0x06
SETUP_RETR = 0x04
STATUS = 0x07
FIFO_STATUS = 0x17
RX_PW_P0 = 0x11
RX_PW_P1 = 0x12
RX_PW_P2 = 0x13
RX_PW_P3 = 0x14
RX_PW_P4 = 0x15
RX_PW_P5 = 0x16
RX_ADDR_P0 = 0x0A
RX_ADDR_P1 = 0x0B
RX_ADDR_P2 = 0x0C
RX_ADDR_P3 = 0x0D
RX_ADDR_P4 = 0x0E
RX_ADDR_P5 = 0x0F
TX_ADDR = 0x10

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 7629

def write(input):
    msb = input >> 8
    lsb = input & 0xFF
    GPIO.output(CS_PIN, GPIO.LOW)
    spi.xfer([lsb])
    GPIO.output(CS_PIN, GPIO.HIGH)
#MSbit first
def set_cs(level):
	if level == 1:
		GPIO.output(CE_PIN, GPIO.HIGH)
	elif level == 0:
		GPIO.output(CE_PIN, GPIO.LOW)
	else:
		raise ValueError('Level must be only 0 or 1.')   
 
def write_reg(reg,data):
	bufer = [(WRITE_MASK | reg),data]
	GPIO.output(CS_PIN, GPIO.LOW)
	spi.xfer2(bufer)
	GPIO.output(CS_PIN, GPIO.HIGH)
	
def read_reg(reg):
	bufer = [(READ_MASK | reg), 0xFF]
	GPIO.output(CS_PIN, GPIO.LOW)
	data = spi.xfer2(bufer)
	GPIO.output(CS_PIN, GPIO.HIGH)
	if reg == STATUS:
		return data[0]
	else:
		return data[1]
	
def set_ce(level):
	if level == 1:
		GPIO.output(CE_PIN, GPIO.HIGH)
	elif level == 0:
		GPIO.output(CE_PIN, GPIO.LOW)
	else:
		raise ValueError('Level must be only 0 or 1.')

def write_payload(data):
	buf = [W_PAYLOAD]
	for n in data:
		t = type(n)
		if t is str:
			buf.append(ord(n))
		elif t is int:
			buf.append(n)
		else:
			raise Exception("Only ints and chars are supported: Found " + str(t))
	GPIO.output(CS_PIN, GPIO.LOW)		
	spi.xfer2(buf)
	GPIO.output(CS_PIN, GPIO.HIGH)
	
def read_payload(payload_l):
	buf = [NOP for i in range(0, payload_l + 1)]
	buf[0] = R_PAYLOAD
	GPIO.output(CS_PIN, GPIO.LOW)
	data = spi.xfer2(buf)
	GPIO.output(CS_PIN, GPIO.HIGH)
	data.pop(0)
	return data

def get_rx_payload_size():
	buf = [R_RX_PL_WID]
	buf.append(NOP)
	GPIO.output(CS_PIN, GPIO.LOW)
	data = spi.xfer2(buf)
	GPIO.output(CS_PIN, GPIO.HIGH)
	return data
	
def flush_tx():
	GPIO.output(CS_PIN, GPIO.LOW)		
	spi.xfer2([FLUSH_TX])
	GPIO.output(CS_PIN, GPIO.HIGH)
	
def flush_rx():
	GPIO.output(CS_PIN, GPIO.LOW)		
	spi.xfer2([FLUSH_RX])
	GPIO.output(CS_PIN, GPIO.HIGH)

def powerUp():
        write_reg(0, read_reg(0) | 0x2)
        time.sleep(150 / 1000000.0)
def powerDown():
        write_reg(0, read_reg(0) & 0xFD)
        time.sleep(150 / 1000000.0)

def set_channel(ch):
	write_reg(RF_CH,ch)

def get_channel():
	return read_reg(RF_CH)	
	
def print_address_reg(reg):
	#P0,P1
	buf = [(READ_MASK | reg)]
	buf.append(NOP)
	if reg==0x0A or reg==0x0B or reg==0x10:
		buf.append(NOP)
		buf.append(NOP)
		buf.append(NOP)
		buf.append(NOP)
	GPIO.output(CS_PIN, GPIO.LOW)
	data = spi.xfer2(buf)
	GPIO.output(CS_PIN, GPIO.HIGH)
	data.pop(0)
	sys.stdout.write(" 0x")
	for i in data:
		sys.stdout.write("%0x" % i)
	sys.stdout.write("\n")

def write_address_reg(reg, data):
	bufer = [(WRITE_MASK | reg)]
	for n in data:
		bufer.append(n)
	spi.xfer2(bufer)

def print_power():
	data = (read_reg(RF_SETUP) >> 1) & 0x3
	if data == 3:
		print("Power: 0dBm")
	elif data == 2:
		print("Power: -6dBm")
	elif data == 1:
		print("Power: -12dBm")
	elif data == 0:
		print("Power: -18dBm")	

def set_power(power_bits):
	power_bits = power_bits << 1
	data = read_reg(RF_SETUP) & 0xF8 #clear power bits
	write_reg(RF_SETUP, data | power_bits)

def print_info():
	print("Status: ", hex(read_reg(STATUS)))
	sys.stdout.write("Address P0: ")
	print_address_reg(RX_ADDR_P0)
	sys.stdout.write("Address P1: ")
	print_address_reg(RX_ADDR_P1)
	sys.stdout.write("Address P2: ")
	print_address_reg(RX_ADDR_P2)
	sys.stdout.write("Address P3: ")
	print_address_reg(RX_ADDR_P3)
	sys.stdout.write("Address P4: ")
	print_address_reg(RX_ADDR_P4)
	sys.stdout.write("Address P5: ")
	print_address_reg(RX_ADDR_P5)
	sys.stdout.write("Address TX: ")
	print_address_reg(TX_ADDR)
	print("Channel: " + hex(get_channel()))
	print("Config: " + hex(read_reg(CONFIG)))
	print("EN_AA: " + hex(read_reg(EN_AA)))
	print("EN_RXADDR: " + hex(read_reg(EN_RXADDR)))
	print("RF_SETUP: " + hex(read_reg(RF_SETUP)))

def ToRXmode():
	data = read_reg(CONFIG)
	data = data | 0x01
	write_reg(CONFIG, data)
	set_ce(1)
	time.sleep(1)

def begin():
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(IRQ_PIN, GPIO.IN)
	GPIO.setup(CS_PIN, GPIO.OUT)
	GPIO.setup(CE_PIN, GPIO.OUT)
	GPIO.output(CE_PIN, GPIO.LOW)
	GPIO.output(CS_PIN, GPIO.HIGH)
	powerUp()
	flush_rx()
	flush_tx()
	write_reg(EN_AA,0x02)
	write_reg(EN_RXADDR,0x02)
	write_reg(SETUP_AW,0x03)
	write_reg(SETUP_RETR,0x5F)
	set_channel(0x4C)
	write_reg(STATUS,0x70)
	write_reg(RF_SETUP,0x20)
	write_reg(RX_PW_P1,3)#payload size
	write_reg(RX_PW_P0,3)#payload size
	new = [0xb3,0xb4,0xb5,0xb6,0xf1]
	#new = [0xb3,0xb4,0x01]
	write_address_reg(RX_ADDR_P1, new)
	write_address_reg(RX_ADDR_P0, new)
	write_address_reg(TX_ADDR, new)
	ToRXmode()
	#write_reg(RF_SETUP,0x06)
	
try:
	begin()
	if LStatus:
		print_info()
	now = datetime.datetime.now()
	if LStatus:
		print(str(now) + " Start listening")
	while(1):
		#data = read_reg(FIFO_STATUS)
		#print(hex(data))
		#data = read_reg(CONFIG)
		#print("STATUS:" + str(hex(data)))		
		#print(GPIO.input(IRQ_PIN))
		if GPIO.input(IRQ_PIN) == 0:
			data = read_reg(STATUS)
			pipe_n = (data >> 1) & 0x7
			if pipe_n == 0x7:
				if LStatus:
					print(str(datetime.datetime.now()) + " Oops! RX_FIFO is empty")
			else:
				if LStatus:
					print(str(datetime.datetime.now()) + " Data from pipe #",str(pipe_n))
			if data & 0x40 != 0:
				rx = read_payload(3)
				msg = ""
				for i in rx:
					msg += chr(i)
				print(msg)
				
				if msg == "alm":	
					if os.path.exists(motion_id):
						#command = ['python3.6','/home/pi/telegram_sender.py', "Обнаружено движение!"]
						command = ['python3','/home/pi/SmartHome/notify_sender.py']
						if LStatus:
							print(str(datetime.datetime.now()) + " launched notify sender")
						#result = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True)
						#print(result)
				
				write_reg(STATUS,0x40)
				#powerDown()
				time.sleep(5)
				#powerUp()
		time.sleep(1)
		


	
	#print(get_status())
	
	#write_payload("T")
	#print("after")
	#print(read_reg(23))
	#flush_tx()

	
except KeyboardInterrupt:
	spi.close()


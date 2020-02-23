from guizero import App, Text, Box
import time

app = App("Датчики", height=200, width=200, layout="grid")

temp = 25
hum = 34

def update():
	global temp
	global hum
	temp += 1
	hum -= 1
	temp_s = "Температура " + str(temp) + " C"
	hum_s = "Влажность " + str(hum) + " %"
	msg_t.clear()
	msg_h.clear()
	msg_t.append(temp_s)
	msg_h.append(hum_s)
	# recursive call
	msg_t.after(1000, update)


temp_s = "Температура " + str(temp) + " C"
hum_s = "Влажность " + str(hum) + " %"
msg_t = Text(app, text=temp_s, grid=[0,0])
msg_h = Text(app, text=hum_s, grid=[0,1])
msg_t.after(1000,update)


app.display()


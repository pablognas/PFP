from math import exp

super_capacitor = 1
time_slice = 0.1
send_time_slice = 3e-3
active_mode = 8e-3
sleep_mode = 20e-6
listen_mode = 19.7e-3
send_mode = 17.4e-3
harvesting = 12e-3
data_acq = 2.5e-3
led_on = 2e-3

texto = ""
log = ""

'''
def capacitor_discharge(capacitance, current_now, current_then):
    """
    Calculate the voltage across a capacitor as it discharges through a resistor.

    :param voltage: The initial voltage across the capacitor.
    :param capacitance: The capacitance of the capacitor.
    :param resistance: The resistance of the resistor.
    :param time: The time elapsed since the start of the discharge.
    :return: The voltage across the capacitor at the given time.
    """

    return (current_now-current_then)/capacitance
'''
def capacitor_sim(capacitance, current_now, current_then):
    """
    Calculate the voltage across a capacitor as it charges through a resistor.

    :param voltage: The initial voltage across the capacitor.
    :param capacitance: The capacitance of the capacitor.
    :param resistance: The resistance of the resistor.
    :param time: The time elapsed since the start of the charge.
    :return: The voltage across the capacitor at the given time.
    """
    return (current_now+current_then)/capacitance

class Node:
    def __init__(self, id, energia = 3):
        global harvesting
        self.id = id
        self.cap_voltage = energia
        self.current = harvesting
        self.led = [False, False, False]    # Red, Yellow, Green
        if energia > 0:
            self.active = True
        else:
            self.active = False

#"<<: clock 0 12344 :>>"
# "<<: init col lines maxTime:>>"
# "<<: end 0 0 :>>"
# "<<: start 11 :>>"
# "<<: stop 11 :>>"
# "<<: leds 11 3 :>>"
# "<<: radio 11 21 :>>"
# "<<: radio 11 65535 :>>"
# "<<: sensor 11 temp :>>"
# "<<: sensor 11 photo :>>"

    def handle_clock(self,time):
        global texto, super_capacitor, active_mode, listen_mode, time_slice, harvesting, sleep_mode, log
        #print( super_capacitor, active_mode, listen_mode, time_slice, harvesting, sleep_mode)
        if self.active:
            ddp_listen = capacitor_sim(super_capacitor,active_mode+listen_mode,self.current)
            print(ddp_listen)
            #print(f"Node {self.id} handled clock. Remaining energy: {self.cap_voltage}")
            log += f"Node {self.id} handled clock at {time}. Remaining energy: {self.cap_voltage}\n"
            leds = 0
            for el in self.led:
                if el:
                    leds += 1
            if leds > 0:
                ddp_leds = capacitor_sim(super_capacitor, leds*led_on, self.current)
            else:
                ddp_leds = 0
            self.current= active_mode+listen_mode+leds*led_on - harvesting
            self.cap_voltage = self.cap_voltage - ddp_leds - ddp_listen
            print(ddp_listen, ddp_leds)
            if self.cap_voltage <=0:
                self.active = False
                log += f"Node {self.id} is now inactive.\n"
                self.cap_voltage = 0
                self.current = harvesting - sleep_mode
        else:
            if self.cap_voltage > 2.1:
                self.active = True
                #print(f"Node {self.id} is now active.")
                log += f"Node {self.id} is now active.\n"
            harvested = capacitor_sim( super_capacitor, harvesting-sleep_mode, self.current)
            print(harvested)
            self.cap_voltage = self.cap_voltage + harvested
        if self.cap_voltage > 3.3:
            self.cap_voltage = 3.3
        texto += f"{float(time/100)}, {self.cap_voltage}\n"
    
    def handle_start(self):
        global log
        self.active = True
        #print(f"Node {self.id} is now active.")
        log += (f"Node {self.id} is now active.\n")
    
    def handle_stop(self):
        global log
        self.active = False
        #print(f"Node {self.id} is now inactive.")
        log += (f"Node {self.id} is now inactive.\n")
    
    def handle_leds(self, led):
        global log
        self.led[led-1] = not self.led[led-1]
        #print(f"Node {self.id} changed the state of LED {led}.")
        log += (f"Node {self.id} changed the state of LED {led}.\n")
    
    def handle_radio(self, to):
        global log
        global texto, super_capacitor, send_mode
        if self.active:
            #print(f"Node {self.id} sent a message to node {to}. Remaining energy: {self.cap_voltage}")
            ddp_send = capacitor_sim(super_capacitor,send_mode,self.current)
            self.current += send_mode
            self.cap_voltage -= ddp_send
            log += (f"Node {self.id} sent a message to node {to}. Remaining energy: {self.cap_voltage}\n")
        else:
            #print(f"Node {self.id} is inactive and cannot send a message.")
            log += (f"Node {self.id} is inactive and cannot send a message.\n")

    def handle_sensor(self, sensor):
        global texto, super_capacitor, data_acq, log
        if self.active:
            self.cap_voltage = capacitor_sim(self.cap_voltage, super_capacitor, data_acq)
            #print(f"Node {self.id} acquired data from sensor {sensor}. Remaining energy: {self.cap_voltage}")
            log += (f"Node {self.id} acquired data from sensor {sensor}. Remaining energy: {self.cap_voltage}\n")
        else:
            #print(f"Node {self.id} is inactive and cannot acquire data.")
            log += (f"Node {self.id} is inactive and cannot acquire data.\n")


with open("log_msg.txt", "r") as file:
    lines = file.readlines()

for line in lines:
    if "<<: init" in line:
        node = Node(10*int(line.split()[2])+int(line.split()[3]))
    elif "<<: clock" in line:
        #print(line.split())
        node.handle_clock(int(line.split()[3]))
    elif "<<: start" in line:
        node.handle_start()
    elif "<<: stop" in line:
        node.handle_stop()
    elif "<<: leds" in line:
        node.handle_leds(int(line.split()[3]))
    elif "<<: radio" in line:
        node.handle_radio(int(line.split()[2]))
    elif "<<: sensor" in line:
        node.handle_sensor(line.split()[2])

with open("log_msg.csv", "w") as file:
    file.write(texto)

with open("log_output_msg.txt", "w") as file:
    file.write(log)


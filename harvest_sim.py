from math import exp

# defining current driven by each action
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

# set up variables to gather output file content
texto = ""
log = ""

def capacitor_sim(capacitance, current_now, current_then):
    """
    Calculate the voltage spent or generated based on the current through the capacitor.
    :param capacitance: The capacitance of the capacitor.
    :param current_now: The current going through the capacitor at this moment.
    :param current_then: The current going through the capacitor at the previous moment.
    :return: The voltage spent or generated on the capacitor at the given time.
    """
    return (current_now+current_then)/capacitance

class Node:
    def __init__(self, id, energia = 3):
        """
        Create Node object
        As default, a node is set up with maximum voltage stored.
        """
        global harvesting
        self.id = id
        self.cap_voltage = energia
        self.current = harvesting
        self.led = [False, False, False]    # Red, Yellow, Green
        if energia > 0:
            self.active = True
        else:
            self.active = False

# Those are the log messages template:
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
        """
        Handle the clock cycle for the node, updating its energy and status.
        The function calculates the energy spent on listening and LED operations, 
        adjusts the current and capacitor voltage, and manages the node's active state.
        
        :param time: The current time step or clock cycle.
        :return: None. This function modifies the internal state of the node.
        
        The process includes:
        - Calculating the energy spent on listening (ddp_listen) based on the active mode and listen mode.
        - Calculating the energy spent on LEDs (ddp_leds) based on the number of active LEDs.
        - Adjusting the node's current based on the active modes, LEDs, and harvesting state.
        - Updating the node's capacitor voltage after considering energy expenditure.
        - If the capacitor voltage reaches 0 or below, the node is deactivated.
        """
        global texto, super_capacitor, active_mode, listen_mode, time_slice, harvesting, sleep_mode, log
        if self.active:
            ddp_listen = capacitor_sim(super_capacitor,active_mode+listen_mode,self.current)
            print(ddp_listen)
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
                log += f"Node {self.id} is now active.\n"
            harvested = capacitor_sim( super_capacitor, harvesting-sleep_mode, self.current)
            print(harvested)
            self.cap_voltage = self.cap_voltage + harvested
        if self.cap_voltage > 3.3:
            self.cap_voltage = 3.3
        texto += f"{float(time/100)}, {self.cap_voltage}\n"
    
    def handle_start(self):
        """
        Activate the node and log the status change.
        
        :return: None. This function modifies the internal state of the node and updates the global log.
        """
        global log
        self.active = True
        log += (f"Node {self.id} is now active.\n")
    
    def handle_stop(self):
        """
        Dectivate the node and log the status change.
        
        :return: None. This function modifies the internal state of the node and updates the global log.
        """
        global log
        self.active = False
        log += (f"Node {self.id} is now inactive.\n")
    
    def handle_leds(self, led):
        """
        Toggle the state of a specific LED on the node and log the status change.
        
        :param led: The index of the LED to toggle (1-based index).
        :return: None. This function modifies the internal state of the node and updates the global log.
        """
        global log
        self.led[led-1] = not self.led[led-1]
        log += (f"Node {self.id} changed the state of LED {led}.\n")
    
    def handle_radio(self, to):
        """
        Handle sending a message from the node to another node and log the status change.
        The energy spent on sending the message is calculated based on the send mode and current. 
        The capacitor voltage is then reduced accordingly.
        
        :param to: The ID of the recipient node to which the message is being sent.
        :return: None. This function modifies the internal state of the node and updates the global log.
        """
        global log
        global texto, super_capacitor, send_mode
        if self.active:
            ddp_send = capacitor_sim(super_capacitor,send_mode,self.current)
            self.current += send_mode
            self.cap_voltage -= ddp_send
            log += (f"Node {self.id} sent a message to node {to}. Remaining energy: {self.cap_voltage}\n")
        else:
            log += (f"Node {self.id} is inactive and cannot send a message.\n")

    def handle_sensor(self, sensor):
        """
        Handle acquiring data from a sensor and log the status change.
        The energy spent on acquiring data is calculated based on the capacitor voltage and data acquisition rate.
        The capacitor voltage is then adjusted accordingly.
        
        :param sensor: The ID or identifier of the sensor from which data is being acquired.
        :return: None. This function modifies the internal state of the node and updates the global log.
        """
        global texto, super_capacitor, data_acq, log
        if self.active:
            self.cap_voltage = capacitor_sim(self.cap_voltage, super_capacitor, data_acq)
            log += (f"Node {self.id} acquired data from sensor {sensor}. Remaining energy: {self.cap_voltage}\n")
        else:
            log += (f"Node {self.id} is inactive and cannot acquire data.\n")


with open("log_msg.txt", "r") as file:
    lines = file.readlines()

for line in lines:
    if "<<: init" in line:
        node = Node(10*int(line.split()[2])+int(line.split()[3]))
    elif "<<: clock" in line:
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


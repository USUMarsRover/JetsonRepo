#!/usr/bin/env python

from __future__ import print_function


#This program is designed to grab usb controller inputs and convert them into commands
#	for a connected Arduino Mega2560 to turn into motor PWM signals.

#This program will not work without the Arduino also being configured with the
#	associated Motor_Control.ino file using the Arduino IDE.

#This program is also designed to use the Logitech Game Controller
#	The controller uses the left axis for forward/reverse movement,
#		and the right axis for left/right turns

#If another controller is used, the Controller_Mapping program can
#	be used to map the button/axis layout of the controller

#This program uses the provided Arduino, which is named in the system
#To name another device, use the following Linux commands while your device is connected
#	dmesg | grep tty
#		The above command lists the ports of the currently connected devices
#	udevadm info --name=/dev/ttyACM0 --attribute-walk
#		This command lists the attributes of your connected device
#		ttyACM0 is the port your device is currently connected in, change it accordingly
#	sudo gedit /etc/udev/rules.d/11-usb-serial.rules
#		This command opens a file with gedit
#		The file creates a symbolic link with listed device
#		Edit the file with information from the udevadm command
#		Example: The file used by the current system has the following information
#			KERNELS=="1-2", ATTRS{serial}=="5583832363535120A161", ATTRS{idVendor}=="2341", SYMLINK+="Main_Arduino"
#				The  SYMLINK is what you wish to name your device as
#	sudo udevadm trigger
#		This command loads the file into the system
#		Reconnect your device after running this command
#	ls /dev
#		If you look through the alphabetized list and see your device name, it worked

# The key functions are:
#	sendToArduino(str) which sends the given string to the Arduino. The string may 
#					   contain characters with any of the ascii values 0 to 255
#
#	recvFromArduino()  which returns an array.
#						 The first element contains the number of bytes that the Arduino said it included in
#							 message. This can be used to check that the full message was received.
#						 The second element contains the message as a string


# the overall process followed by the demo program is as follows
#   open the serial connection to the Arduino - which causes the Arduino to reset
#   wait for a message from the Arduino to give it time to reset
#	initialized the connected controller using pygame
#   loop through the current input states of the controller
#		generate commands based on the input states
#		send the commands to the Arduino
#		wait for a reply and display it on the PC

# the message to be sent to the Arduino starts with < and ends with >
#	the message content comprises two integers
#	the numbers are sent as their ascii equivalents

# receiving a message from the Arduino involves
#	waiting until the startMarker is detected
#	saving all subsequent bytes until the end marker is detected

import rospy
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Joy

#=====================================

#  Function Definitions

#=====================================

def sendToArduino(sendStr):
	ser.write(sendStr.encode('utf-8')) # change for Python3


#======================================

def recvFromArduino():
	global startMarker, endMarker
	
	ck = ""
	x = "z" # any value that is not an end- or startMarker
	byteCount = -1 # to allow for the fact that the last increment will be one too many
	
	# wait for the start character
	while  ord(x) != startMarker: 
		x = ser.read()
	
	# save data until the end marker is found
	while ord(x) != endMarker:
		if ord(x) != startMarker:
			ck = ck + x.decode("utf-8") # change for Python3
			byteCount += 1
		x = ser.read()
	
	return(ck)


#============================

def waitForArduino():

	# wait until the Arduino sends 'Arduino Ready' - allows time for Arduino reset
	# it also ensures that any bytes left over from a previous message are discarded
	
	global startMarker, endMarker
	
	msg = ""
	while msg.find("Arduino is ready") == -1:

		while ser.inWaiting() == 0:
			pass
		
		msg = recvFromArduino()

		print (msg) # python3 requires parenthesis
		print ()
		
#======================================

def run_motors(td):
	numLoops = len(td)
	waitingForReply = False

	n = 0
	while n < numLoops:
		teststr = td[n]

		if waitingForReply == False:
			sendToArduino(teststr)
			result = [x.strip() for x in teststr.split(',')]
			print("Left Speed: " + result[0].replace('<','') + "   Right Speed: " + result[1].replace('>','') + "     ", end='\r')
			waitingForReply = True

		if waitingForReply == True:

			while ser.inWaiting() == 0:
				pass
			
			dataRecvd = recvFromArduino()
			n += 1
			waitingForReply = False


#======================================

# THE PROGRAM STARTS HERE

#======================================

import serial
import time
#import pygame
#pygame.init()
# These are the import statements to use in the ROS portion of the program
import rospy
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Joy

print ()
print ()

# This section opens the serial port to the Arduino
# NOTE the user must ensure that the serial port and baudrate are correct
serPort = "/dev/Main_Arduino"
baudRate = 9600
ser = serial.Serial(serPort, baudRate)
print ("Serial port " + serPort + " opened  Baudrate " + str(baudRate))

#Config for how fast the motors spin, choose a number between 0 and 100
speed = 50

#Variable default initialization
startMarker = 60
endMarker = 62
going = True
left_speed = str(0)
right_speed = str(0)
temp_left = 0
temp_right = 0
global pos1
global pos2
pos1 = 0
pos2 = 0

waitForArduino()

#global testData = []

#Receives joystick messages (subscribed to Joy topic)
#then converts the joystick inputs into Twist commands
#axis 1 aka left stick vertical controls linear speed
#axis 3 aka left stick horizontal controls angular speed
def callback(data):
	# global pos1, pos2
        twist = Twist()
        #twist.linear.x = data.axes[1]
        #twist.angular.z = data.axes[3]
	pos1 = int(data.axes[1]*(speed))
	pos2 = int(data.axes[3]*(-speed))
	print("pos1: ",pos1)
	print("pos2: ",pos2)
	#print(twist)
        #pub.publish(twist)

	#Loop until quit command is entered (currently command is not configured)
#	while(going):
	#Initialization of data storage and joystick
	#NOTE that this assumes only one controller is connected
	#joy_count = pygame.joystick.get_count()
	#print(joy_count)
	testData = []
	#joystick = pygame.joystick.Joystick(0)
	#joystick.init()
	#Grab the events that record which buttons and axes are pressed
	#No data is stored, this just prompts the joystick to make its data accessible
	#for event in pygame.event.get(): 
	#	if event.type == pygame.QUIT:
	#		pygame.quit()

	#Grab the current positions of each joystick
	#pos1 = int(joystick.get_axis(1)*(-speed))
	#pos2 = int(joystick.get_axis(3)*speed)

	


	#Set a resting point at 0 for situations when the axes slightly off center
	if (pos1 < 3) and (pos1 > -3):
		pos1 = 0
	if (pos2 < 3) and (pos2 > -3):
		pos2 = 0
	
	#Generate motor speeds based off joystick positions
	#First check is for moving in one direction
	if (pos1 != 0) and (pos2 == 0):
		temp_left = pos1
		temp_right = pos1
	#Second check is for turning without moving in a direction
	elif (pos1 == 0) and (pos2 != 0):
		#Right turn
		if (pos2 > 0):
			temp_left = int(pos2)
			temp_right = int(pos2*(-1))
		#Left turn
		if (pos2 < 0):
			temp_left = int(pos2)
			temp_right = int(pos2*(-1))
	#Third check is for when turning and moving in a direction
	elif (pos1 != 0) and (pos2 != 0):
		#Right turn
		if (pos1 > 0):
			temp_left = int((pos1 + pos2) / 2)
			temp_right = int((pos1 - pos2) / 2)
		#Left turn
		else:
			temp_left = int((pos1 - pos2) / 2)
			temp_right = int((pos1 + pos2) / 2)
	#Final check is for not moving or turning (resting)
	else:
		temp_left = 0
		temp_right = 0

	#Send data to Arduino
	left_speed = str(temp_left)
	right_speed = str(temp_right)
	print("left_speed before send:",left_speed)
	print("right_speed before send:",right_speed)
	testData.append("<"+left_speed+","+right_speed+">")
	run_motors(testData)

def listener():
	#Grabbing joystick data from the ROS topic /joy AKA we're making a listener
	# publishing to "motorcontrol/cmd_vel" to control motors
	global pub
	print("after made global pub")
	pub = rospy.Publisher('motorcontrol/cmd_vel', Twist, queue_size=10)
	# starts the node
	print("just before initializing node")
	rospy.init_node('Joy2Motor')
	# subscribed to joystick inputs on topic "joy"
	print("just before rospy.Subscriber")
	rospy.Subscriber("joy", Joy, callback)
	print("just after rospy.Subscriber")
	rospy.spin()

	print("END OF LISTENER")

if __name__ == "__main__":
	listener()

ser.close



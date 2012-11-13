from vesna import alh
from vesna.alh.spectrumsensor import SpectrumSensor, SpectrumSensorProgram
from vesna.alh.signalgenerator import SignalGenerator, SignalGeneratorProgram, TxConfig
from vesna.alh.common import log

import os
import string
import sys
import time

def get_communicator_url():
	try:
		credentials = open("credentials").read().strip() + "@"
	except IOError:
		credentials = ""

	return "https://%scrn.log-a-tec.eu/communicator" % (credentials,)

def main():
	coor_industrial_zone = alh.ALHWeb(get_communicator_url(), 10001)
	coor_industrial_zone._log = log

	time_start = time.time() + 15

	# Set up transmissions

	cognitive_terminal = SignalGenerator(alh.ALHProxy(coor_industrial_zone, 25))

	config_list = cognitive_terminal.get_config_list()
	device_config = config_list.get_config(0, 0)

	cognitive_terminal.program( SignalGeneratorProgram(
		TxConfig(device_config, 110, 0),
		time_start=(time_start+5), 
		time_duration=25))

	cognitive_terminal.program( SignalGeneratorProgram(
		TxConfig(device_config, 225, 0),
		time_start=(time_start+32), 
		time_duration=23))


	legacy_terminal = SignalGenerator(alh.ALHProxy(coor_industrial_zone, 16))

	legacy_terminal.program( SignalGeneratorProgram(
		TxConfig(device_config, 114, 0),
		time_start=(time_start+25),
		time_duration=30))

	# Set up spectrum sensing

	sensor_node_ids = [ 2, 17, 6 ]

	sensor_nodes = [ alh.ALHProxy(coor_industrial_zone, id) for id in sensor_node_ids ]
	sensors = [ SpectrumSensor(sensor_node) for sensor_node in sensor_nodes ]

	config_list = sensors[0].get_config_list()
	sweep_config = config_list.get_config(0, 0).get_full_sweep_config()

	program = SpectrumSensorProgram(sweep_config, time_start, time_duration=60, slot_id=5)

	for sensor in sensors:
		sensor.program(program)

	
	# Wait for the experiment to finish

	for sensor in sensors:
		while not sensor.is_complete(program):
			print "waiting..."
			time.sleep(2)

			if time.time() > (program.time_start + program.time_duration + 60):
				raise Exception("Something went wrong")

		print "experiment is finished. retrieving data."

		result = sensor.retrieve(program)

		try:
			os.mkdir("data")
		except OSError:
			pass

		result.write("data/node_%d.dat" % (sensor.alh.addr,))

main()

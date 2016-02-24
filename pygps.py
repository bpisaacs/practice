import time
import serial
import pynmea2

start_time = time.time()
run_time = 0
time_allowed = 60
soak_time = 15

com = "COM1"
baud = 115200
conn = serial.Serial(com, baud)

gps_fix = 0
num_of_satellites = 0
snr_count = 0
msg_num = 0

#Pass/Fail Status
fix_status = False
num_of_satellites_status = False
snr_count_status = False
raim_status = False

def has_test_passed():
	has_passed = False
	if fix_status == True and num_of_satellites_status == True:
		if snr_count_status == True and raim_status == True:
			has_passed = True
	return has_passed

def parse_fw_version(NMEA):
	delimiters_to_fw = 9
	for i in range(delimiters_to_fw):
		skip = NMEA.find(",") + 1
		NMEA = NMEA[skip:]
	end_parse = NMEA.find(",")
	fw_version = float(NMEA[:end_parse]) / 100.0
	return fw_version

def get_raim_status(NMEA):
	raim_pass = 0
	raim_status = False
	for i in range(7):
		skip = NMEA.find(",") + 1
		NMEA = NMEA[skip:]
		end_parse = NMEA.find(",")
		raim_field = int(NMEA[:end_parse])
		if raim_field > 0: raim_pass += 1
	if raim_pass >= 3: 
		print "RAIM status cofirmed"
		raim_status = True
	return raim_status

def find_gps_fix_status(NMEA):
	fix_status = find_gps_fix_status(NMEA)
	if "GSA" in NMEA:
		parsed = pynmea2.parse(NMEA)
		gps_fix = int(parsed.mode_fix_type)
	if gps_fix !=3 and run_time > soak_time:
		print "Test failed, could not establish GPS fix in time."
		break
	elif gps_fix == 3 and fix_status == False:
		print "GPS Fix achieved"
		fix_status = True
	return fix_status
	
def find_snr_count(NMEA):
	snr_count = 0
	if "GSV" in NMEA:
		parsed = pynmea2.parse(NMEA)
		
		#check for sattelite signal strength
		num_of_snrs = int(parsed.num_messages)
		msg_num = int(parsed.msg_num)
		#each GSV message contains up to 4 sattelite SNRs
		for i in range(0,num_of_snrs):
			#pynmea uses the snr_1, snr_2, etc.... attribute to grab signal strength
			command = "snr_" + str(i+1)
			#SNR is a measure of signal strength, analgous to C/No
			snr = int(getattr(parsed, command))
			if snr >= 46: snr_count +=1	

def find_sattelite_count(NMEA)
	if "GSV" in NMEA:	
	parsed = pynmea2.parse(NMEA)
	num_of_satellites = int(parsed.num_sv_in_view)	
	return num_of_satellites
#Main loop	
while run_time < time_allowed:
	if not snr_count: snr_count = 0
	current_time = time.time()
	run_time = round(current_time - start_time, 0)
	NMEA = conn.readline()
	
	fix_status = find_gps_fix_status(NMEA)
	if run_time > soak_time: 
		snr_count += find_snr_count(NMEA)	
		num_of_satellites = find_sattelite_count(NMEA)
			
if num_of_satellites > 10 and num_of_satellites_status == False:
	print str(num_of_satellites) + " satellite sources located."
	num_of_satellites_status = True
				
	if "RAIM" in NMEA and raim_status == False:
		fw_version = parse_fw_version(NMEA)
		print "Firmware version: " + str(fw_version)
		raim_status = get_raim_status(NMEA)
	if snr_count >= 2 and snr_count_status == False:
		print str(snr_count) + " sattelites with an SNR of 46 or greater found!"
		snr_count_status = True
	#reset snr count if we're at the last GSV message
	if msg_num == (num_of_satellites / 4) + 1:
		snr_count = 0
	if has_test_passed():
		print "GPS-2020 has passed EIT!  Shiver me timbers what a swell program this is!"
		break
	if run_time > time_allowed:
		print "GPS-2020 EIT failed."
	
conn.close()
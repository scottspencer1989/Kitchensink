import subprocess
import sys
import re
import io

class throttle:

	#self.bw=["5Mbit/s","4Mbit/s","3Mbit/s","2Mbit/s","1Mbit/s"]

	def __init__(self):
		#self.bw=["5Mbit/s","4Mbit/s","3Mbit/s","2Mbit/s","1Mbit/s"]
		self.bw=["5000Kbit/s","4000Kbit/s","3000Kbit/s","2000Kbit/s","1000Kbit/s"]
		#self.maxt=300
	
	def stop(self):
		#Quietly (-q) flush all pipes (-F all) and disable pfctl (-d)
		subprocess.run(["pfctl", "-q", "-F", "all", "-d"])
		subprocess.run(["dnctl", "-q", "flush"])
		print("Throttle removed")
	
	# ./toggle_proxy.sh off; pkill -2 -f 'python myproxy_csv.py';)&
	
	
	
	# Starting BW
	def start(self):
		#Set the connection speed on the pipe
		subprocess.run(["dnctl", "pipe", "1", "config", "bw", self.bw[0]])
		print("Speed set to: " + self.bw[0])

		#The companion script routes all packets through a pipe controlled by dnctlchmod
		subprocess.run(["./dummyscript.sh"], shell=True)
		#print("This prints if dummyscript works")
		
		#Enable pfctl (-e) quietly (-q)
		subprocess.run(["sudo","pfctl", "-e", "-q"])
		#print("This prints if pfctl enables")
	
		# Run a wireshark capture in parallel
		# wireshark -i en0  -k -a duration:$MAX_T -w dumpcap
	def set(self, gear):
		subprocess.run(["dnctl", "pipe", "1", "config", "bw", self.bw[gear]])
		print("Speed set to: " + self.bw[gear])
	
def csvtest(dur, infile):
	
	#Monitor total bits received over interval. infile delivers cumulative bits received
	baseline=0
	bits=0

	#Threshold are in Mbps, used to control throttling, and values have been experimentally determined.
	High_Threshold=1.5
	Med_Threshold=1
	Low_Threshold=.5
	
	input=io.open(infile,'r')

	#could do this bit with just first and last lines
	#input[-1] - input[0]

	for line in input:
		try:
			#Regular expression to select the time from the input
			match=re.search('[0-9]{2}\.[0-9]{6}',line)
			time=match.group(0)
			time=int(round(float(time)))
			
			#Regular expression to select in received bytes from the input
			match=re.search('[0-9]+$',line)
			bytesin=int(match.group(0))
			
			#Input bytes are cumulative totals, we treat our fist sample as a first
			#baseline and use subsequent samples to compute the difference over time
			if baseline==0:
				baseline=bytesin
				bitsin=0
			else:
				#Convert byte total into bits since last sample
				bitsin=(bytesin-baseline)*8
				baseline=bytesin
			
			#running total of receive bits 
			bits+=bitsin
		except:
			print('Operation isn\'t working\n')
	
	#compute the average and convert to Mbps		
	ave=(bits/dur)/1000000

	if ( ave >= High_Threshold ):
		Flag="high"
	elif ( ave < Low_Threshold):
		Flag="low"
	else:
		Flag="medium"
	return Flag	

def main():
	my_session=throttle()
	dur=20
	readfile="netstats.csv"
	counter=0
	active=True
	gear=0

	active=True
	print("Start Throttling")
	my_session.start()
	gear=0

	while True:
		try:
				subprocess.check_output(['./nettap.sh '], shell=True)
				Flag=csvtest( dur,readfile )

				if ( Flag== "high" ) and ( active == False ):
					active=True
					print("Start Throttling")
					my_session.start()
					gear=0
					
					#Throttleling logic here
				elif (active == False ):
					print("No need to throttle")
				elif ( Flag=="high" ) and ( active == True ):
					print("More Throttle")
					if gear<4 :
						gear+=1
					my_session.set(gear)

				
				elif ( Flag=="medium"):
					print("This is fine")
					#if gear<4 :
					#	gear+=1
					#my_session.set(gear)
					#print("Throttling anyway though")
	
				elif ( Flag== "low" ):
					if gear>1:
						print("Less Throttle")
						gear-=2
					elif gear>0:
						gear=0
					elif gear==0:
						active=False
						print("Stop Throttling")
						#my_session.stop()
					my_session.set(gear)
				else:
					print("Flag error")

		except KeyboardInterrupt:
			print("Thanks for playing - program closing")
			my_session.stop()
			break
		except Exception as e:
			print("Oh snap, theres an error")
			print(e)
			my_session.stop()
			break

if __name__ == '__main__':
	main()
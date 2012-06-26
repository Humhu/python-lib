import math

SIN_POINTS = 257;
ASIN_POINTS = 256;
ATAN_POINTS = 256;
NUM_COLS = 10;

lookup_file = open("lookup_32.txt", 'w');

lookup_file.write("Sine Table\n")
# Lookup index ranges from 0x000 (0) to 0x400 (256)
# 	for a total of 257 angles
# i will range from [0, SIN_POINTS - 1]
# We want arg to range from [0.0, pi/2]
step = (math.pi/2)/(SIN_POINTS - 1);
col_num = 0;
for i in range(0, SIN_POINTS):
	arg = i*(math.pi/2)/(SIN_POINTS - 1);
	val = math.sin(arg);
	lookup_file.write(str(val) + ", ")
	col_num = col_num + 1;
	if col_num == NUM_COLS:
		col_num = 0;
		lookup_file.write("\n")


lookup_file.write("\n\nAsine Table\n")
# i will range from [0, ASIN_POINTS - 1]
# We want arg to range from [0.0, 1.0]
step = 1.0/(ASIN_POINTS - 1);
rad_to_bams = 65536/(2*math.pi);
col_num = 0;	
for i in range(0, ASIN_POINTS):
	arg = i*step;
	val = math.asin(arg);
	b = int(math.floor(val*rad_to_bams));
	lookup_file.write(hex(b) + ", ")
	col_num = col_num + 1;
	if col_num == NUM_COLS:
		col_num = 0;
		lookup_file.write("\n")
	

lookup_file.write("\n\nAtan Table\n")
# i will range from [0, ATAN_POINTS - 1]
# We want arg to range from [0.0, 1.0]
step = 1.0/(ATAN_POINTS - 1);
rad_to_bams = 65536/(2*math.pi);
col_num = 0;
for i in range(0, ATAN_POINTS):
	arg = i*step;
	val = math.atan(arg);
	b = int(math.floor(val*rad_to_bams));
	lookup_file.write(hex(b) + ", ")
	col_num = col_num + 1;
	if col_num == NUM_COLS:
		col_num = 0;
		lookup_file.write("\n")
		
lookup_file.close();
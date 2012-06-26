# Behavior constants defined here

YawPIDParams = {

    'Ref':0,
    'Offset':0,
    'Kp':20,
    'Ki':10,
    'Kd':18,
    'Beta':1,
    'Gamma':0

}

PitchPIDParams = {

    'Ref':0.78,
    'Offset':80,
    'Kp':20,
    'Ki':4,
    'Kd':6,
    'Beta':1,
    'Gamma':0

}

RollPIDParams = {

    'Ref':0.0,
    'Offset':0,
    'Kp':0,
    'Ki':0,
    'Kd':0,
    'Beta':0,
    'Gamma':0

}

BehaviorStates = {
	0:'Tracking', 
	1:'Reacquiring', 
	2:'Searching', 
	3:'Circling'
}

RegulatorStates = {

    'Off':0,
    'Stabilize':1,
    'Remote Control':2,

}

Commands = {	
    
    'ECHO':0x1F,      # send back the received packet

	'SET_REGULATOR_STATE':0x21,
	'SET_REGULATOR_REF':0x22,
	'SET_REGULATOR_PID':0x23,
	'SET_REGULATOR_RATE_FILTER':0x24,
    'SET_RC_VALUES':0x25,

    'RECORD_SENSOR_DUMP':0x28,
    'GET_MEM_CONTENTS':0x29,
	'RUN_GYRO_CALIB':0x2A,
	'GET_GYRO_CALIB_PARAM':0x2B,
    
	'SET_ESTIMATE_RUNNING':0x2C,
    'REQUEST_TELEMETRY':0x2D,
    'RESPONSE_TELEMETRY':0x2E,
    'RECORD_TELEMETRY':0x2F,
    
	'ADDRESS_REQUEST':0x30,
	'ADDRESS_OFFER':0x31,
	'ADDRESS_ACCEPT':0x32,

    'DIR_UPDATE_REQUEST':0x34,
    'DIR_UPDATE_RESPONSE':0x35,
    'DIR_DUMP_REQUEST':0x36,
    'DIR_DUMP_RESPONSE':0x37,
    
	'CLOCK_UPDATE_REQUEST':0x38,
    'CLOCK_UPDATE_RESPONSE':0x39,
    
    'RAW_FRAME_REQUEST':0x40,
    'RAW_FRAME_RESPONSE':0x41,
    'CENTROID_REPORT':0x42,
    'SET_BACKGROUND_FRAME':0x43,
    'CAM_PARAM_REQUEST':0x48,
    'CAM_PARAM_RESPONSE':0x49,
    
    'SET_HP':0x4A,
}
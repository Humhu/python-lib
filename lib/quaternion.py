from math import *

def eulerToQuaternion(yaw, pitch, roll):
    psi_2 = yaw/2.0
    theta_2 = pitch/2.0
    phi_2 = roll/2.0
    
    w = cos(phi_2)*cos(theta_2)*cos(psi_2) + \
        sin(phi_2)*sin(theta_2)*sin(psi_2)
    x = sin(phi_2)*cos(theta_2)*cos(psi_2) - \
        cos(phi_2)*sin(theta_2)*sin(psi_2)
    y = cos(phi_2)*sin(theta_2)*cos(psi_2) + \
        sin(phi_2)*cos(theta_2)*sin(psi_2)
    z = cos(phi_2)*cos(theta_2)*sin(psi_2) - \
        sin(phi_2)*sin(theta_2)*cos(psi_2)
        
    return (w, x, y, z)

def eulerToQuaternionDeg(yaw, pitch, roll):
    return eulerToQuaternion(radians(yaw), radians(pitch), radians(roll))
    
    
    
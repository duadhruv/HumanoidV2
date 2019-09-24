from __future__ import division
import bluetooth
import threading

import time
import sys
import Adafruit_PCA9685
import pymssql
import MySQLdb



inputcomp = False
servo_min = 140  # Min pulse length out of 4096
servo_max = 590  # Max pulse length out of 4096
prevangle=[-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]
inipos="90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90;"
iniposarray=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
delta=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
currdelta=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
ang=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]



pwm = Adafruit_PCA9685.PCA9685()
pwm.set_pwm_freq(60)

def getinipos():
    
    db = MySQLdb.connect("localhost", "sa", "123hex", "Humanoid2")
    curs=db.cursor()
    curs.execute("Select inipos from init_pos;")
    res=curs.fetchall()
    for row in res:
        print("reading init pos")
        #print(row[0])
        serialprint(row[0])
        inipos = row[0]
        
        
        
    
    curs.close()
    db.close()
    return inipos

def saveinipos(pos):
    global inipos
    db = MySQLdb.connect("localhost", "sa", "123hex", "Humanoid2",autocommit=True)
    curs=db.cursor()
    query = "call update_inipos('{}');".format(pos)
    print(query)
    curs.execute(query)
    #db.commit()
    res=curs.fetchall()
    curs.close()
    db.close()
    
def insertmove(movename,value):
    global inipos
    db = MySQLdb.connect("localhost", "sa", "123hex", "Humanoid2",autocommit=True)
    curs=db.cursor()
    query = "call new_move('{}','{}');".format(movename,value)
    print(query)
    curs.execute(query)
    #db.commit()
    res=curs.fetchall()
    curs.close()
    db.close()
def getmove(movename):
    db = MySQLdb.connect("localhost", "sa", "123hex", "Humanoid2")
    curs=db.cursor()
    query = "Select posn from {} order by id asc;".format(movename)
    curs.execute(query)
    res=curs.fetchall()
    i=0
    deltas=[]
    for row in res:
        print("reading init pos")
        #print(row[0])
        serialprint(row[0])
        deltas.append(row[0])
        i=i+1 
    curs.close()
    db.close()
    return deltas
    

def pulsewidth(value):
    global servo_min,servo_max 
    leftSpan = 180
    rightSpan = servo_max-servo_min
    valueScaled = float(value) / float(leftSpan)
    return int(servo_min + (valueScaled * rightSpan))

def mirror(l):
    r=[]
    for i in range(len(l)):
        if i in [0,1,2,3,4,10,12,15]:
            r.append(180-l[i])
	else:
            r.append(l[i])
    return r


def serialread(s):
    sl = s.split(",")
    s=[]
    for i in range(16):
        #print(s1[i])
        s.append(int(sl[i]))
    return s#mirror(s)


def serialprint(msg):
    global client_sock,connected
    msg=str(msg)
    print(msg)
    msg=msg+"\n"
    if(connected):
        client_sock.send(msg)


def inputservo(ang,a):
    global pwm,prevangle
    msg=""
    if a==0:
	msg = "fast moving"
    else:
	msg = "slow moving"
    if prevangle[0]!=-1:
        #serialprint("/////////////////////////////////////////////")
        for i in range(16):
	    if ang[i]!=prevangle[i]:
                serialprint(msg+" "+str(i)+"-"+str(ang[i]))
                prevangle[i]=ang[i]
		if ang[i]==-2 or ang[i]==182:
		    pwm.set_pwm(i,0,0)
		else:
		    pwm.set_pwm(i,0,pulsewidth(ang[i]))
		    time.sleep(a)
    else:
        for i in range(16):
            prevangle[i]=ang[i]
	    serialprint(msg+" "+str(i)+"-"+str(ang[i]))
	    pwm.set_pwm(i, 0, pulsewidth(ang[i]))
	    time.sleep(a)


    
   ## pwm.set_pwm(i, 0, 0)


def detach():
    global pwm,prevangle
    for i in range(16):
        pwm.set_pwm(i, 0, 0)
        prevangle[i]=-1
        time.sleep(0.01)


def startup():
    global ang,pwm,inipos
    detach()
    inipos = getinipos()
    #inipos=inipos[:-1]
    ang=serialread(inipos[:-1])
    inputservo(ang,0.1)
def smartmove(newdelta,t):
    global ang,pwm,currdelta
    t=t*10
    angpersec = [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
    print(currdelta)
    for i in range(16):
        angpersec[i] = (newdelta[i]-currdelta[i])/t
        print(angpersec[i])
    while(t is not 0):
        #print("while exec")
        for p in range(16):
            if(angpersec[p] is not 0):
                na = float(float(ang[p])+angpersec[p])
                pwm.set_pwm(p,0,pulsewidth(na))
                ang[p]=na
                #sprint(str(na))
        t=t-1
        #if()
        calc_delta()
        time.sleep(0.01)
            
    
def calc_delta():
    global currdelta,ang,iniposarray
    for p in range(16):
        currdelta[p]=ang[p]-iniposarray[p]
def calc_ang_fromdelta(deltas):
    currang=[]
    for p in range(16):
        currang=iniposarray[p]+deltas[p]
    return currang

def tilt():
    global ang
    posns=["67,60,109,79,74,102,97,105,85,108,84,115,75,23,140,6",
           "80,60,109,79,74,115,97,105,85,121,84,115,75,23,140,6S1",
           "80,60,109,79,74,115,97,105,85,85,84,115,75,23,60,86S2"]
           #"51,60,109,79,46,111,97,105,85,80,84,115,75,23,140,6S",
           #"51,60,109,79,46,111,97,105,85,80,84,115,75,23,60,94"]
           #"51,60,109,79,22,111,97,105,85,88,84,115,75,23,60,94"]
    for i in range(3):
        if(posns[i][-2:-1]=="S"):
            print("smartmove")
            t=int(posns[i][-1])
            posns[i]=posns[i][:-2]
            angs=serialread(posns[i])
            smartmove(angs,t)
            
        else:
            angs=serialread(posns[i])
            ##pwm.set_pwm(i,0,pulsewidth(angs))
            inputservo(angs,0)
            ang=angs
            time.sleep(0.5)
    time.sleep(2)
    for i in reversed(range(3)):
        if(posns[i][-2:-1]=="S"):
            print("smartmove")
            t=int(posns[i][-1])
            posns[i]=posns[i][:-2]
            angs=serialread(posns[i])
            smartmove(angs,t)
            
        else:
            angs=serialread(posns[i])
            ##pwm.set_pwm(i,0,pulsewidth(angs))
            inputservo(angs,0)
            ang=angs
            time.sleep(0.5)        
            
            
def exec_move_reverse(movename):
    global ang
    deltas = getmove(movename)
    size=len(deltas)
    for i in range(size):
        if(deltas[i][-2:-1]=="S"):
            print("smartmove")
            t=int(deltas[i][-1])
            input=deltas[i][:-2]
            delta=serialread(input)
            print(input)
            smartmove(delta,t)
            
        else:
            d=serialread(deltas[i])
            ##pwm.set_pwm(i,0,pulsewidth(angs))
            for i in range(16):
                newang[i]=ang[i]+d[i]
            inputservo(newang,0)
            ang=newang
            time.sleep(0.5)
            calc_delta()

    time.sleep(2)
    for p in reversed(range(size)):
        if(deltas[p][-2:-1]=="S"):
            print("smartmove")
            t=int(deltas[p][-1])
            input=deltas[p][:-2]
            delta=serialread(input)
            print(input)
            smartmove(delta,t)
            
        else:
            d=serialread(deltas[p])
            ##pwm.set_pwm(i,0,pulsewidth(angs))
            for i in range(16):
                newang[i]=ang[i]+d[i]
            inputservo(newang,0)
            ang=newang
            time.sleep(0.5)
            calc_delta()

def exec_move(movename):
    global ang
    deltas = getmove(movename)
    size=len(deltas)
    for i in range(size):
        if(deltas[i][-2:-1]=="S"):
            print("smartmove")
            t=int(deltas[i][-1])
            input=deltas[i][:-2]
            delta=serialread(input)
            print(input)
            smartmove(delta,t)
            if(i==(len(deltas)-1)):
                print_ang_list(ang)
            
        else:
            d=serialread(deltas[i])
            ##pwm.set_pwm(i,0,pulsewidth(angs))
            for i in range(16):
                newang[i]=ang[i]+d[i]
            inputservo(newang,0)
            ang=newang
            time.sleep(0.5)
            calc_delta()
            if(i==(len(deltas-1))):
                print_ang_list(ang)
        
    


def print_ang_list(ang):
    output=""
    for i in range(16):
        if(i is not 15):
            output=output+str(int(ang[i]))
            output=output+","
        else:
            output=output+str(int(ang[i]))
            output=output+";"
    serialprint("printing curr positions")
    serialprint(output)

def get_last_step(movename):
    deltas = getmove(movename)
    if(deltas[len(deltas)-1][-2:-1]=="S"):
        print("smartmove")
        t=int(deltas[len(deltas)-1][-1])
        input=deltas[len(deltas)-1][:-2]
        delta=serialread(input)
        print(input)
        smartmove(delta,t)
        angs=calc_ang_fromdelta(delta)
        print_ang_list(angs)
        

        
    
        


    

while(1):
    server_sock=bluetooth.BluetoothSocket( bluetooth.RFCOMM )
    port = 1
    lastpos=""
    server_sock.bind(("",port))
    server_sock.listen(1)
    client_sock,address = server_sock.accept()
    print "Accepted connection from ",address
    connected = True
    data = ""
    while(1):
        try:
            if(connected):
                if(not inputcomp):
                    data = data + client_sock.recv(1)
                    if(data[-1] == ";"):
                        read = data[:-1]
                        data = ""
                        print(read)
                        inputcomp = True
                        
                if(inputcomp):
                    for p in range(16):
                        currdelta[p]=ang[p]-iniposarray[p]
                    if(read=="start"):
                        #print("start function call")
                        startup()
                        iniposarray=serialread(inipos[:-1])
                        #serialprint("startup")
                    elif(read=="detach"):
                        detach()
                        serialprint("detach")
                        #print("detach function call")
                    elif(read=="saveinit"):
                        saveinipos(lastpos+";")
                        iniposarray=serialread(lastpos)
                        #print("saveinit function call")
                    elif(read=="tilt"):
                        tilt()
                    elif(read[0]=="$"):
                        read=read[1:]
                        value=""
                        iniposarray=serialread(inipos[:-1])
                        for p in range(16):
                            delta[p]=ang[p]-iniposarray[p]
                        for i in range(16):
                            if(i is not 15):
                                value= value+ str(delta[i])+","
                            else:
                                value= value + str(delta[i])
                        if(read[-2:-1]=="S"):
                            t=(read[-1])
                            value=value+"S"+t
                            movename=read[:-2]
                            
                        print(value)
                        insertmove(movename,value)
                    elif(read[0]=="#"):
                        if(read[-1]=="R"):
                            movename=read[1:][:-1]
                            exec_move_reverse(movename)
                        else:
                            movename=read[1:]
                            exec_move(movename)
                    elif(read[0]=="!"):
                        movename=read[1:][:-1]
                        get_last_step(movename)
                    else :
                        lastpos=read
                        ang=serialread(read)
                        print("positions recieved")
                        inputservo(ang,0)
                    inputcomp = False
                    
                        
        
        
        except(bluetooth.btcommon.BluetoothError):
            print("connection from user disconnected")
            connected = False
            break
        except(KeyboardInterrupt, SystemExit):
            print("detaching servos")
            detach()
            sys.exit()
        
            
        

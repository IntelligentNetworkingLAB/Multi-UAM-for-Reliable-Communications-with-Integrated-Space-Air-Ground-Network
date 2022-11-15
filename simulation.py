from operator import index
import random as rand
import math
import numpy as np
from random import *
from matplotlib import pyplot as plt
import copy
import time
import pandas as pd
import onnx
import torch
import onnxruntime as ort

onnx_path = "real3.onnx"
ort_sess = ort.InferenceSession(onnx_path)

g_0 = 2.0
sigma = 174
alpha = 0.7
p_0 = 4.0
w_0 = 30e3

UAVNUM = 3
BSNUM = 6
curpts = []
endpts = []
bspts = []
isdone = [False for _ in range(UAVNUM)]

datarate = [0 for _ in range(UAVNUM)]

rem_inputs = [0 for _ in range(150)]

memory = [[],[],[]]

def Euclidean(p, q):
    return math.sqrt(math.pow(p[0]-q[0],2) + math.pow(p[1]-q[1],2))

def EuclideanHeight(p, q):
    return math.sqrt(math.pow(p[0]-q[0],2) + math.pow(p[1]-q[1],2) + math.pow(70,2))

def clamp(num, min_value, max_value):
   return max(min(num, max_value), min_value)

def GetDataRate():
   for i in range(UAVNUM):
        mindis = EuclideanHeight(curpts[i], bspts[0])
        for j in range(BSNUM):
            tmpdis = EuclideanHeight(curpts[i], bspts[j])
            if(mindis > tmpdis):
                mindis = tmpdis
        gain = g_0 / pow(mindis, alpha)
        sinr = ( p_0 * gain) / sigma
        datarate[i] = max(w_0 * math.log(1 + sinr), 60)
   return

def make_inputs(idx, iter):
    global rem_inputs

    #rem_inputs = rem_inputs[30:]
    rem_inputs=[]
    rem_inputs = rem_inputs + curpts[idx]
    rem_inputs = rem_inputs + ([endpts[idx][j] - curpts[idx][j] for j in range(2)])
    for i in range(UAVNUM):
        if i==idx: continue
        rem_inputs = rem_inputs + ([curpts[i][j] - curpts[idx][j] for j in range(2)])
    #for i in range(BSNUM):
        #rem_inputs = rem_inputs + ([bspts[i][j] - curpts[idx][j] for j in range(2)])
    #print(rem_inputs)
    return [rem_inputs]

def Trajectory(idx, iter):
    global curpts
    outputs = ort_sess.run(None, {'obs_0': make_inputs(idx, iter)})
    out = [clamp(outputs[2][0][0], -1.0, 1.0), clamp(outputs[2][0][1], -1.0, 1.0)]
    curpts[idx][0] += out[0] * 25.0
    curpts[idx][1] += out[1] * 25.0

def IsDone():
    for i in range(UAVNUM):
        if isdone[i]==False:
            if(Euclidean(curpts[i], endpts[i]) <= 50):
                isdone[i]=True
            else: return False
    return True

def Initialize():
    curpts.append([-230, -230])
    curpts.append([-230, 230])
#    curpts.append([-230, 0])
    endpts.append([230, 230])
    endpts.append([230, -230])
#    endpts.append([230, 0])
    isdone[0] = False
    isdone[1] = False
#    isdone[2] = False
    bspts.append([-125, 125])
    bspts.append([-125, -125])
    bspts.append([0, -125])
#    bspts.append([125, -125])
#    bspts.append([125, 0])
#    bspts.append([125, 125])
    return

if __name__ == '__main__':
    mm = [[] for _ in range(UAVNUM)]
    Initialize()
    iter = 0
    for _ in range(200):
        if IsDone(): break
        #print("iteration")
        for i in range(3):
            if isdone[i]: continue
            Trajectory(i, iter)
            mm[i].append([curpts[i][0], curpts[i][1]])
        GetDataRate()
        print(datarate)
        iter += 1
        
    for m in mm:
        print("UAV")
        for i in m:
            print(i[0], i[1])

    print("base station")
    for me in bspts:
        print(me[0], me[1])
    
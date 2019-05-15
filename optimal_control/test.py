"""
Example script for animating a model
"""
import numpy as np
import scipy.integrate as integrate
import scipy.interpolate as interpolate

from pyoviz.BiorbdViz import BiorbdViz
import biorbd

import matplotlib.pyplot as plt

# Load the biorbd model

m = biorbd.s2mMusculoSkeletalModel("Modeles/ModeleSansMuscle.s2mMod")

nFrame = 500            # number of frames
nNoeuds = 30                # number of points
nMuscle = m.nbTau()
nPhase = 1
nPoints = (nPhase*nNoeuds)+1
nQtotal = m.nbQ()+m.nbQdot()

##### State from the file

fichierS = open("Resultats/StatesSansMuscle.txt", "r")

i = 0
t = []                                      # initialization of the time

all_Q = np.ones((m.nbQ(), nPoints))             # initialization of the states nbQ lines and nbP columns
all_Qdot = np.ones((m.nbQdot(), nPoints))

# initialization of the derived states

# Nnoeuds first lines
for l in range(nNoeuds):
    ligne = fichierS.readline()
    lin = ligne.split('\t')                 # separation of the line in element
    lin[:1] = []                            # remove the first element ( [ )
    lin[(nPhase*m.nbQ()) + (nPhase*m.nbQdot()) + 1:] = []     # remove the last ( ] )

    t.append(float(lin[0]))                                                         # complete the time with the first column
    for p in range(nPhase):
        all_Q[:, i+p*nNoeuds] = [float(j) for j in lin[1+p*nQtotal:m.nbQ()+p*nQtotal+1]]                              # complete the states with the nQ next columns
        all_Qdot[:, i+p*nNoeuds] = [float(k) for k in lin[m.nbQ()+1+p*nQtotal:nQtotal*(p+1)+1]]        # complete the states with the nQdot next columns

    i += 1
# Last line
ligne = fichierS.readline()
lin = ligne.split('\t')                 # separation of the line in element
lin[:1] = []                            # remove the first element ( [ )
lin[(nPhase*m.nbQ()) + (nPhase*m.nbQdot()) + 1:] = []     # remove the last ( ] )
t.append(float(lin[0]))
all_Q[:, -1] = [float(j) for j in lin[1+(nPhase-1)*nQtotal:m.nbQ()+(nPhase-1)*nQtotal+1]]                              # complete the states with the nQ next columns
all_Qdot[:, -1] = [float(k) for k in lin[m.nbQ()+1+(nPhase-1)*nQtotal:nQtotal*nPhase+1]]


fichierS.close()

# Complete the time
for p in range(1, nPhase):
    for i in range(nNoeuds):
        t.append(p+t[i+1])

##### Controls from the file

fichierU = open("Resultats/ControlsSansMuscle.txt", "r")

i = 0
all_U = np.ones((nMuscle, nPoints))          # initialization of the controls

for l in range(nNoeuds):
    ligne = fichierU.readline()
    lin = ligne.split('\t')
    lin[:1] = []
    lin[(nPhase*nMuscle) + 1:] = []

    for p in range(nPhase):
        all_U[:, i+p*nNoeuds] = [float(i) for i in lin[1+p*nMuscle:nMuscle*(p+1)+1]]

    i += 1

ligne = fichierU.readline()
lin = ligne.split('\t')
lin[:1] = []
lin[(2*nMuscle) + 1:] = []

all_U[:, -1] = [float(i) for i in lin[1+(nPhase-1)*nMuscle:nMuscle*nPhase+1]]

fichierU.close()

#### integration

# #dynamique sans muscle
def dyn(t_int, X):

    QDDot = biorbd.s2mMusculoSkeletalModel.ForwardDynamics(m, X[:m.nbQ()], X[m.nbQ():], u).get_array()
    rsh = np.ndarray(m.nbQ() + m.nbQdot())
    for i in range(m.nbQ()):
        rsh[i] = X[m.nbQ()+i]
        rsh[i + m.nbQ()] = QDDot[i]

    return rsh

# u=np.array([8.6843e-01])
# X=np.array([1.7794e-01, -1.0142, 1.0794, -4.0377])
# print(dyn(0, X))

X = np.concatenate((all_Q[:, 0], all_Qdot[:, 0]))
print("Solution initiale: ", X)
u = all_U[:, 0]
print("Control: ", u)
print("Tstart: ", t[0], "\nTend: ", t[1])
LI = integrate.solve_ivp(dyn, (t[0], t[1]), X)
T = LI.t.tolist()[0:len(LI.t.tolist())-1]
I = LI.y[:, 0:len(T)]
print("Fin integration reelle: ", LI.y[:, -1])
print("Fin integration theorique(noeuds suivant): ", np.concatenate((all_Q[:, 1], all_Qdot[:, 1])))
print("\n")

for interval in range(1, len(t)-1):                 # integration between each point
    u = all_U[:, interval]
    X = np.concatenate((all_Q[:, interval], all_Qdot[:, interval]))
    print("Solution initiale: ", X)
    print("Control: ", u)
    print("Tstart: ", t[interval], "\nTend: ", t[interval+1])
    LI = integrate.solve_ivp(dyn, (t[interval], t[interval+1]), X)
    I = np.concatenate((I, LI.y[:, 0:len(LI.t.tolist())-1]), axis=1)
    print("Fin integration reelle: ", LI.y[:, -1])
    print("Fin integration theorique(noeuds suivant): ", np.concatenate((all_Q[:, interval+1], all_Qdot[:, interval+1])))
    print("\n")
    for i in range(len(LI.t)-1):
        T.append(LI.t.tolist()[i])


#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
'''
Created on Oct 24, 2013

@author: jpmena
'''

from xml.etree.ElementTree import iterparse
from datetime import datetime
import math


#tiré de la page 186 de Python CookBook Third Edition
def parse_and_remove(filename):
    saxpath=['{http://www.topografix.com/GPX/1/1}trk', '{http://www.topografix.com/GPX/1/1}trkseg', '{http://www.topografix.com/GPX/1/1}trkpt']
    doc = iterparse(filename, ('start', 'end'))
    # Skip the root element
    next(doc)
    tag_stack = []
    elem_stack = []
    for event, elem in doc:
        if event == 'start':
            tag_stack.append(elem.tag)
            elem_stack.append(elem)
        elif event == 'end':
            if tag_stack == saxpath:
                yield elem #permet d'être utilisé dans une boucle cf. p 593 de Learning Python Fifth Edition
                elem_stack[-2].remove(elem)
            try:
                tag_stack.pop()
                elem_stack.pop()
            except IndexError:
                pass

#http://effbot.org/zone/element.htm
def recupere_donnees(element):
    retour = {}
    try:
        retour['latitude'] = float(element.get('lat'))
        retour['longitude'] = float(element.get('lon'))
    except ValueError as ve:
        print ("impossible de calculer latitude ou longitude car non décimal: message {0}\n".format(ve))
    for ele in element.getchildren():
        if ele.tag == '{http://www.topografix.com/GPX/1/1}time':
            try:
                retour['date']=datetime.strptime(ele.text,'%Y-%m-%dT%H:%M:%SZ')
            except ValueError as ve:
                print("impossible de recupere la date du point: message {0}\n".format(ve))
    return retour

def calcule_distance_parcourue(donnees_avant,donnees_actuelles):
    #http://www.ga.gov.au/earth-monitoring/geodesy/geodetic-techniques/distance-calculation-algorithms.html
    #on se base sur le sphérical algorithm cf. mail avec Nicolas: les distances entre les points sont de quelques mètres
    #la distance calculée est directement en kilomètres
    distance=None
    vitesse = -1
    if 'longitude' in donnees_avant.keys() and donnees_avant['longitude'] is not None:
        G1=math.radians(donnees_avant['longitude'])
        if 'longitude' in donnees_actuelles.keys() and donnees_actuelles['longitude'] is not None:
            G2=math.radians(donnees_actuelles['longitude'])
            DG=math.radians(G2-G1)
            if 'latitude' in donnees_avant.keys() and donnees_avant['latitude'] is not None:
                L1=math.radians(donnees_avant['latitude'])
                if 'latitude' in donnees_actuelles.keys() and donnees_actuelles['latitude'] is not None:
                    L2=math.radians(donnees_actuelles['latitude'])
                    DL=math.radians(L2-L1)
                    #D = 1.852 * 60 * ARCOS ( SIN(L1) * SIN(L2) + COS(L1) * COS(L2) * COS(DG))
                    #D = 1.852 * 60 * math.acos( math.sin(L1) * math.sin(L2) + math.cos(L1) * math.cos(L2) * math.cos(DG))
                    TERM1 = 111.08956 * (DL + 0.000001)
                    TERM2 = math.cos(L1 + (DL/2))
                    TERM3 = (DG + 0.000001) / (DL + 0.000001)
                    D = TERM1 / math.cos(math.atan(TERM2 * TERM3))
                    distance = 100 * D #correction arbitraire pour avoir le résultat en kilomètres apparemment
                    if 'date' in donnees_avant.keys() and donnees_avant['date'] is not None:
                        if 'date' in donnees_actuelles.keys() and donnees_actuelles['date'] is not None:
                            delta = donnees_actuelles['date'] - donnees_avant['date']
                            vitesse = distance / (delta.total_seconds() / 3600)
                        else:
                            print ("timestamp du point 2 absente\n")
                    else:
                        print ("timestamp du point 1 absente\n")
                else:
                    print ("latitude du point 2 absente\n")
            else:
                print ("latitude du point 1 absente\n")
        else:
            print ("longitude du point 2 absente\n")
    else:
        print ("longitude du point 1 absente\n")
    return (distance , vitesse)
if __name__ == '__main__':
    path_gpx = "/home/jpmena/RSM/GPXTEsts/GPXFiles/seance du 21 oct 2013.gpx"
    points=[]
    for domElem in parse_and_remove(path_gpx):
        points.append(recupere_donnees(domElem))
    print ("il y a {0} points\n".format(len(points)))
    #nous allons calculer la distance cumulée et l'enregistrer(la formule nous a retourné la distance directement en kms)
    dout_path='%s.dplot' %(path_gpx)
    dplot = open(dout_path, 'w')
    vout_path='%s.vplot' %(path_gpx)
    vplot = open(vout_path, 'w')
    avancees = []
    vitesses = []
    pavant = None
    prise_vitesse_avant = (None,0)  #le datetime de prise de la vitesse avant et la distance cumulée correspondante
    davant=0
    calcul_vitesse_tous_les_m = 50 #on ne meseure la vitesse que tous les 50m
    for p in points:
        avancee = {}
        velem = {}
        delta = 0
        vitesse = -1
        if pavant is not None:
            (delta,vitesse) = calcule_distance_parcourue(pavant,p)
        else:
            prise_vitesse_avant = (p['date'],0)
        avancee['d'] = delta
        avancee['v'] = vitesse
        avancee['dc'] = davant + delta
        avancee['t'] = p['date']
        delta_pour_vitesse = avancee['dc'] - prise_vitesse_avant[1]
        if delta_pour_vitesse >= (calcul_vitesse_tous_les_m / 1000) and avancee['v'] > 0 and prise_vitesse_avant[0] is not None: 
            velem['t'] = p['date']
            delta_t = velem['t'] - prise_vitesse_avant[0]
            velem['v'] = delta_pour_vitesse / (delta_t.total_seconds() / 3600)
            vitesses.append(velem)
            vplot.write("{0} {1}\n".format(velem['t'].strftime("%H:%M:%S"),velem['v']))
            print ("{0} {1}\n".format(velem['t'].strftime("%H:%M:%S"),velem['v']))
        pavant = p
        davant = avancee['dc']
        avancees.append(avancee)
        dplot.write("{0} {1} {2}\n".format(avancee['t'].strftime("%H:%M:%S"),avancee['dc'],avancee['v']))
        print("{0} {1} {2}\n".format(avancee['t'].strftime("%H:%M:%S"),avancee['dc'],avancee['v']))        
    print ("il y a {0} distances calculées\n".format(len(avancees)))
    print ("il y a {0} vitesses calculées\n".format(len(vitesses)))
    dplot.close()
    vplot.close()
        
    
        #print 'longitude {lon}'.format({'lon':repr(domElem)})
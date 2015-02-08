# -*- coding: utf-8 -*-
import os
import glob
import time
import subprocess
from pymongo import MongoClient

os.system('sudo modprobe w1-gpio')
os.system('sudo modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'


def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        print("Current temp is: " + str(temp_c))
        date = time.strftime("%Y-%m-%d")
        clocktime = time.strftime("%H:%M:%S")
        #save_temp_to_mongodb(temp_c, date, clocktime)
        truncate_today = save_temp_to_txt(temp_c, date, clocktime)
        coldest, warmest, avg = get_data()
        update_html_file(temp_c, date, clocktime, str(coldest), str(warmest), str(avg))
        if truncate_today: open('today.txt', 'w').close()

def save_temp_to_txt(t, d, c):
    print("Saving " + c + " " + str(t) + " to today.txt")
    with open('today.txt', 'a') as today:
        today.write(c + " " + str(t) + "\n")
    if c[:2] == "23":
        with open('today.txt') as today:
            todaylines = today.readlines()
        print("Number of lines in today.txt: " + str(len(todaylines)))
        print("Archiving today.txt")
        lines = [d]
        for l in todaylines:
            lines.append(l.split()[1])
        with open('archive.txt', 'a') as archive:
            archive.write(' '.join(lines) + "\n")
        return True
    return False

def get_data():
    # Stats today
    coldest = 1000
    warmest = -1000
    average = 0
    today = time.strftime("%Y-%m-%d")
    with open('today.txt') as f:
        lines = f.readlines()
        for line in lines:
            data = line.split()
            temperature = float(data[1])
            if temperature < coldest: coldest = temperature
            if temperature > warmest: warmest = temperature
            average += temperature
        average /= len(lines)
    return coldest, warmest, average

def update_html_file(t, d, c, coldest, warmest, avg):
    head = '<!DOCTYPE html>' \
           '<html>' \
           '<meta charset="UTF-8">' \
           '<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.1/css/bootstrap.min.css">' \
           '<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.1/js/bootstrap.min.js"></script>' \
           '</head>'
    start = "<body>" \
            "<h1>Temperaturen er: " + str(t) + "C.<br />" \
            "Oppdatert: " + d + " " + c + "</h1><br />"
    end = "<p>Kaldeste i dag: " + coldest + "<br />Varmeste i dag: " + warmest + "<br />Gjennomsnittlig temperatur i dag: " + avg + "</p>"
    table = '<h2>Målinger i dag:</h2><br/><table class="table table-striped table-hover" >'

    with open('today.txt') as today:
        for t in today.readlines():
            tt = t.split()
            table += "<tr><td>" + tt[0] + "</td><td>" + tt[1] + "</td></tr>"
        table += "</table>"

    archive = '<br /><h2>Arkiv:</h2><br /><table class="table table-striped table-condensed table-hover">'

    with open('archive.txt') as arch:
        for line in arch.readlines():
            archive += "<tr>"
            e = line.split()
            for i in range(len(e)):
                archive += "<td>" + e[i] + "</td>"
            archive += "</tr>"
        archive += "</table></body></html>"

    with open('/var/www/index.html', 'w') as f:
        f.write(head+start+end+table+archive)

read_temp()
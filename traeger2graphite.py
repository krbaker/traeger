#!/usr/bin/python3
# coding=utf-8

"""
Collects stats from traeger grills

Copyright 2020 by Keith Baker All rights reserved.
This file is part of the traeger python library,
and is released under the "GNU GENERAL PUBLIC LICENSE Version 2". 
Please see the LICENSE file that should have been included as part of this package.
"""
import os
import getpass
import pprint
import traeger
import numbers
import json
import time
import socket

pp = pprint.PrettyPrinter(indent=4)

def unpack(base, value):
    if isinstance(value, numbers.Number):
        if isinstance(value, bool):
            value = int(value)
        return [(".".join(base), value)]
    elif isinstance(value, dict):
        return unpack_dict(base, value)
    elif isinstance(value, list):
        return unpack_list(base, value)
    return []

def unpack_list(base, thelist):
    result = []
    for n, v in enumerate(thelist):
        newbase = base.copy()
        newbase.append(str(n))
        result.extend(unpack(newbase, v))
    return result

def unpack_dict(base, thedict):
    result = []
    for k, v in thedict.items():
        if k == "custom_cook" and len(base) == 1:
            pass
        else:
            newbase = base.copy()
            newbase.append(k)
            result.extend(unpack(newbase, v))
    return result

if __name__ == "__main__":
    try:
        config = json.load(open(os.path.expanduser("~/.traeger"),"r"))
    except (json.JSONDecodeError, FileNotFoundError):
        config = {}
    if "username" not in config:
        config["username"] = input("username:")
    if "password" not in config:
        config["password"] = getpass.getpass()
    if "graphite_port" not in config:
        config["graphite_port"] = input("graphite port:")
    if "graphite_host" not in config:
        config["graphite_host"] = input("graphite host:")

    open(os.path.expanduser("~/.traeger"),"w").write(json.dumps(config))


    t = traeger.traeger(config['username'], config['password'])
    
    while True:
        last_collect = time.time()
        grills = t.get_grills()
        grills_status = t.get_grill_status()
        for grill in grills:
            if grill["thingName"] not in grills_status:
                print ("Missing Data for {}".format(grill["thingName"]))

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((config["graphite_host"], int(config["graphite_port"])))
            for k,v in unpack_dict([], grills_status):
                s.send("traeger.{} {} {}\r\n".format(k, v, int(last_collect)).encode())
            s.close()
        except Exception as e:
            print (e)
        next_collect = last_collect + 60
        until_collect = next_collect - time.time()
        if until_collect > 0:
            print ("Sleeeping {}".format(until_collect))
            time.sleep(until_collect)
        else:
            print ("Late for next collection {}".format(until_collect))
    


#t = traeger.traeger(input("user:"), getpass.getpass())
#grills = t.get_grill_status()
#for k,v in unpack_dict([], grills): 
#    print("{} {}".format(k, v))

        


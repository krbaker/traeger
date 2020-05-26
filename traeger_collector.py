# coding=utf-8

"""
Collects stats from traeger grills

"""
import os
import getpass
import pprint
import traeger
import numbers

import diamond.collector

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

class TraegerCollector(diamond.collector.Collector):

    def get_default_config_help(self):
        config_help = super(TraegerCollector, self).get_default_config_help()
        config_help.update({
            'username': "username to traeger app",
            'password': "password to traeger app",
            'cache': "where to store our creds cache"
        })
        return config_help

    def get_default_config(self):
        """
        Returns the default collector settings
        """
        config = super(TraegerCollector, self).get_default_config()
        config.update({
            'username': None,
            'password': None,
            'cache': None
        })
        return config

    def collect(self):
        t = traeger.traeger(self.config['username'], self.config['password'])
        grills = t.get_grill_status()
        for k,v in unpack_dict([], grills): 
            self.publish(k, v)


#t = traeger.traeger(input("user:"), getpass.getpass())
#grills = t.get_grill_status()
#for k,v in unpack_dict([], grills): 
#    print("{} {}".format(k, v))

        


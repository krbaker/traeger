import os
import getpass
import pprint
import traeger
import numbers

pp = pprint.PrettyPrinter(indent=4)

def unpack(base, value):
    if isinstance(value, numbers.Number):
        if isinstance(value, bool):
            value = int(value)
        print ("{}:{}".format(".".join(base), value))
    elif isinstance(value, dict):
        unpack_dict(base, value)
    elif isinstance(value, list):
        unpack_list(base, value)

def unpack_list(base, thelist):
    for n, v in enumerate(thelist):
        newbase = base.copy()
        newbase.append(str(n))
        unpack(newbase, v)

def unpack_dict(base, thedict):
    for k, v in thedict.items():
        if k == "custom_cook" and len(base) == 1:
            pass
        else:
            newbase = base.copy()
            newbase.append(k)
            unpack(newbase, v)
    
if __name__ == "__main__":
    user = input("Enter Username : ")
    passwd = getpass.getpass()
    t = traeger.traeger(user, passwd)
    grills = t.get_grill_status()
    unpack_dict([], grills)
        


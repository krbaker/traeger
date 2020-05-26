import os
import getpass
import pprint
import traeger

pp = pprint.PrettyPrinter(indent=4)

if __name__ == "__main__":
    user = input("Enter Username : ")
    passwd = getpass.getpass()
    t = traeger.traeger(user, passwd)
    pp.pprint(t.get_grill_status())


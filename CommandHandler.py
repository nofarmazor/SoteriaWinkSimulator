from SoteriaDB import SoteriaConstants, SoteriaDBHandler
import json
import wink
from wink import login, persist
import time


def enum(**enums):
    return type('Enum', (), enums)

Commands = enum(Turn_On='Turn_On', Turn_Off='Turn_Off', Lock='Lock', Unlock='Unlock')
Commands_Payload = enum(Turn_On='{ "desired_state" : { "brightness": "0.9", "powered": "True" }}', Turn_Off='{ "desired_state" : { "brightness": "0.1", "powered": "False" }}', Lock='{ "desired_state" : { "locked": "False" }}', Unlock='{ "desired_state" : { "locked": "False" }}')

# ID Fields for supported devices
LIGHT_BULB_ID = "light_bulb_id"
LOCK_ID = "lock_id"

# Device types:
LIGHT_BULBS = "light_bulbs"
LOCKS = "locks"

# Global API
wink_api = wink.init("config.cfg")

#Device IDs
lock_id= '33713'
light_bulb_id = '595306'

# TODO: login code for token refresh before starting to run the code (with a button)
# TODO: Add alarm change for the door lock
def _refresh_authentication():
    # reauthenticate:
    cf = persist.ConfigFile('config.cfg')
    auth_obj = cf.load()
    if wink.need_to_reauth(**auth_obj):
        wink.reauth(**auth_obj)


def get_device_state(device_cloud_id):
    _refresh_authentication()
    devices = wink_api.get_devices()
    for device in devices:
        if LIGHT_BULB_ID in device:  # light bulb case
            if device[LIGHT_BULB_ID] == device_cloud_id:
                if "powered" in device["desired_state"]:  # device is  pending
                    if device["desired_state"]["powered"]:
                        return Commands.Turn_On
                    else:
                        return Commands.Turn_Off
                else:
                    if device["last_reading"]["powered"]:  # the device is updated check the value in the last reading
                        return Commands.Turn_On
                    else:
                        return Commands.Turn_Off
        if LOCK_ID in device: #door lock case
            if device[LOCK_ID] == device_cloud_id:
                if "locked" in device["desired_state"]:
                    if device["desired_state"]["locked"]:
                        return Commands.Lock
                    else:
                        return Commands.Unlock
                else:
                    if device["last_reading"]["locked"]:
                        return Commands.Lock
                    else:
                        return Commands.Unlock
    raise ValueError("The device ID is not a valid light bulb or a door lock")

def get_device_type_pending_param(device_type):
    if device_type == LIGHT_BULBS:
        return 'powered'
    elif device_type == LOCKS:
        return 'locked'

def is_device_valid(device_cloud_id, device_type):
    """
    Check if the given device exist in wink account
    :param device_cloud_id:
    :return: True if the device id exist, otherwise return false
    """
    try:
        wink_api.get_device_by_id(device_type, device_cloud_id)
        return True
    except Exception as e:
        return False

def change_device_state(device_cloud_id, device_type, command, command_payload):
    _refresh_authentication()
    if not is_device_valid(device_cloud_id, device_type):
        raise ValueError("\nPossible Errors: \n1.Device Cloud ID does not exist in the current wink account"
                         "\n2.Device does not belong to " + str(device_type))

    if get_device_state(device_cloud_id) == command:
        raise Exception("The device is already in its expected state. \n No change was done.")
    else:
        try:
            result = wink_api.update_device_state(device_type, device_cloud_id, command_payload)
        except Exception as e:
            raise Exception("Error occurred while sending a command to Wink API:\n" + e.message)
        try: #check device  status:
            if get_device_state(device_cloud_id) == command:
                SoteriaDBHandler.save_command(device_cloud_id, command)
                return True
            raise Exception("The device did not change it's status, please send command again")
        except Exception as e:
            raise Exception("Error occurred: \n" + e.message)

def get_updated_devices():
    devicesDict = dict()
    devices = wink_api.get_devices()
    for device in devices:
        if LIGHT_BULB_ID in device:
            devicesDict[device[LIGHT_BULB_ID]] = device['manufacturer_device_model']
        if LOCK_ID in device:
            devicesDict[device[LOCK_ID]] = device['manufacturer_device_model']


#result1 = change_device_state('33713', LOCKS, Commands.Unlock, Commands_Payload.Unlock)
#result2 = change_device_state('33713', LOCKS, Commands.Lock, Commands_Payload.Lock)
#result3 = change_device_state('595306', LIGHT_BULBS, Commands.Turn_On, Commands_Payload.Turn_On)
result4 = change_device_state('595306', LIGHT_BULBS, Commands.Turn_Off, Commands_Payload.Turn_Off)
#result = lock("33713")
#print result

from SoteriaDB import SoteriaDBHandler, SoteriaConstants
import json
import wink
from wink import login


#ID Fields for supported devices
LIGHT_BULB_ID = "light_bulb_id"
LOCK_ID = "lock_id"

# Device types:
LIGHT_BULBS = "light_bulbs"
LOCKS = "locks"

#Global API
wink_api = wink.init("config.cfg")

#TODO: login code for token refresh before starting to run the code (with a button)
#TODO: Add alarm change for the door lock

def is_device_turned_on(device_cloud_id):
    """
    Check if the given device id status.
    :param device_cloud_id:
    :return: True if the device is on, otherwise return false
    """
    devices = wink_api.get_devices()
    for device in devices:
        if LIGHT_BULB_ID in device:
            if device[LIGHT_BULB_ID] == device_cloud_id:
                if "powered" in device["desired_state"]: # device is  pending
                    is_on = device["desired_state"]["powered"]
                    break
                else:
                    is_on = device["last_reading"]["powered"] # the device is updated check the value in the last reading
        if LOCK_ID in device:
            if device[LOCK_ID] == device_cloud_id:
                if "locked" in device["desired_state"]:
                    is_on = device["desired_state"]["locked"]
                    break
                else:
                    is_on = device["last_reading"]["locked"]
    if is_on is None:
        raise ValueError("The device ID is not a valid light bulb or a lock")
    return is_on

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
        return False;

def turn_on_light_bulb(device_cloud_id, brightness):
    """
    Turn on light bulb according to device cloud id and store the command in Soteria DB.
    If the light bulb is already turned on, raise an exception
    :param device_cloud_id:
    :return: True if the light bulb was turned successfully, otherwise return False.
    """
    if not is_device_valid(device_cloud_id, LIGHT_BULBS):
        raise ValueError("\nPossible Errors: \n1.Device Cloud ID does not exist in the current wink account"
                         "\n2.Device is not a light bulb")

    # check whether the light bulb is already turned on
    if is_device_turned_on(device_cloud_id):
        raise Exception("The Light Bulb is already On")
    else:
        try:
            # turn on light bulb
            turn_on_command = '{ "desired_state" : { "brightness": "' + brightness + '", "powered": "True" }}'
            result = wink_api.update_device_state(LIGHT_BULBS, device_cloud_id, turn_on_command)
        except Exception as e:
            raise Exception("Error occurred while sending a command to Wink API:\n" + e.message)
        try:
            # check light bulb status
            if "desired_state" in result:
                if (result["desired_state"]["powered"]):

                    #turn on success, store command in DB:
                    SoteriaDBHandler.save_command(device_cloud_id, SoteriaConstants.TURN_ON_COMMAND)
                    return True
                raise Exception("The light bulb did not change its status, please send command again")
        except Exception as e:
            raise Exception("Error occurred: \n" + e.message)


def turn_off_light_bulb(device_cloud_id):
    """
    Turn off light bulb according to device cloud id and store the command in Soteria DB.
    If the light bulb was already off, raise an exception
    :param device_cloud_id:
    :return: True if the light bulb was turn off successfully, otherwise, return false.
    """
    if not is_device_valid(device_cloud_id, LIGHT_BULBS):
        raise ValueError("\nPossible Error:\n1.Device Cloud ID does not exist in the current wink account"
                         "\n2.Device is not a light bulb")

    # check whether the light bulb is already turned off
    if not is_device_turned_on(device_cloud_id):
        raise Exception("The Light Bulb is already Off")
    else:
        try:
            # turn off light bulb
            turn_off_command = '{ "desired_state" : { "brightness": "0.1", "powered": "False" }}'
            result = wink_api.update_device_state(LIGHT_BULBS, device_cloud_id, turn_off_command)
        except Exception as e:
            raise Exception("Error occurred while sending a command to Wink API:\n" + e.message)
        try:
            # check light bulb status
            if "desired_state" in result:
                if not result["desired_state"]["powered"]:

                    #turn off success, store command in DB:
                    SoteriaDBHandler.save_command(device_cloud_id, SoteriaConstants.TURN_OFF_COMMAND)
                    return True
                raise Exception("The light bulb did not change its status, please send command again")
        except Exception as e:
            raise Exception("Error occurred: \n" + e.message)


def lock(device_cloud_id):
    """
    Lock the door lock and store the command in the DB. If the door lock is already locked, raise an exception.
    :param device_cloud_id:
    :return: True if the door lock was locked otherwise return false.
    """
    if not is_device_valid(device_cloud_id, LOCKS):
        raise ValueError("\nPossible Error:\n1.Device Cloud ID does not exist in the current wink account"
                         "\n2.Device is not a Lock")
    # check whether the door lock is already locked
    if is_device_turned_on(device_cloud_id):
        raise Exception("The door lock is already locked")
    else:
        try:
            # lock door lock
            lock_command = '{ "desired_state" : { "locked": "True" }}'
            result = wink_api.update_device_state(LOCKS, device_cloud_id, lock_command)
        except Exception as e:
            raise Exception("Error occurred while sending a command to Wink API:\n" + e.message)
        try:
            # check door lock status
            if "desired_state" in result:
                if result["desired_state"]["locked"]:

                    #lock success, store command in DB:
                    SoteriaDBHandler.save_command(device_cloud_id, SoteriaConstants.LOCK_COMMAND)
                    return True
                raise Exception("The door lock did not change its status, please send command again")
        except Exception as e:
            raise Exception("Error occurred: \n" + e.message)

def unlock(device_cloud_id):
    """
    Unlock the door lock and store the command in the DB. If the door lock is already unlocked, raise an exception.
    :param device_cloud_id:
    :return: True if the door lock was unlocked otherwise return false.
    """
    if not is_device_valid(device_cloud_id, LOCKS):
        raise ValueError("\nPossible Error:\n1.Device Cloud ID does not exist in the current wink account"
                         "\n2.Device is not a Lock")
    # check whether the door lock is already unlocked
    if not is_device_turned_on(device_cloud_id):
        raise Exception("The door lock is already unlocked")
    else:
        try:
            # unlock door lock
            unlock_command = '{ "desired_state" : { "locked": "False" }}'
            result = wink_api.update_device_state(LOCKS, device_cloud_id, unlock_command)
        except Exception as e:
            raise Exception("Error occurred while sending a command to Wink API:\n" + e.message)
        try:
            # check door lock status
            if "desired_state" in result:
                if not result["desired_state"]["locked"]:

                    #unlock success, store command in DB:
                    SoteriaDBHandler.save_command(device_cloud_id, SoteriaConstants.UNLOCK_COMMAND)
                    return True
                raise Exception("The door lock did not change its status, please send command again")
        except Exception as e:
            raise Exception("Error occurred: \n" + e.message)


result = unlock("30012")
print result



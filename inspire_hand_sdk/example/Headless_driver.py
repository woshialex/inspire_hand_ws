# from inspire_dds import inspire_hand_touch,inspire_hand_ctrl,inspire_hand_state
# from inspire_dds import inspire_hand_touch,inspire_hand_ctrl,inspire_hand_state
import sys
from inspire_sdkpy import inspire_sdk,inspire_hand_defaut
import time
# import inspire_sdkpy
if __name__ == "__main__":
    handler=inspire_sdk.ModbusDataHandler(ip=inspire_hand_defaut.defaut_ip,LR='r',device_id=1)
    while True:
        data_dict=handler.read()
        time.sleep(0.02)

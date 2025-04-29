from asyncio import SelectorEventLoop
import multiprocessing
import time
from inspire_sdkpy import qt_tabs,inspire_sdk,inspire_hand_defaut
import sys

def worker(config, use_serial=True, show_touch=True):
    app = qt_tabs.QApplication(sys.argv)
    if not show_touch:
    ## Only publish this data to increase publishing frequency
        selected_states = ['angle_act', 'force_act', 'status']
    else:
        selected_states = None
    if use_serial:
        handler=inspire_sdk.ModbusDataHandler(serial_port=config['serial_port'], LR=config['side'], device_id=config['device_id'], use_serial=True, selected_states=selected_states)
    else:
        handler=inspire_sdk.ModbusDataHandler(ip=config['ip'], LR=config['side'], device_id=config['device_id'],
        selected_states=selected_states)

    window = qt_tabs.MainWindow(data_handler=handler,dt=20,name=f"Hand {config['side']}", run_time=False, Plot_touch=show_touch)
    window.reflash()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    # 使用默认IP地址的示例
    config = {
        'left':{
            'side': 'l',
            'ip': '192.168.123.210',
            'serial_port': '/dev/ttyUSB1',
            'device_id': 1,
        },
        'right':{
            'side': 'r',
            'ip': '192.168.123.211',
            'serial_port': '/dev/ttyUSB0', #insert to USB first
            'device_id': 1, #if connect to same USB, then device id +1
        }
    }
    use_serial = True
    process_l = multiprocessing.Process(target=worker, args=(config['left'], use_serial))
    process_r = multiprocessing.Process(target=worker, args=(config['right'], use_serial))

    process_r.start()
    time.sleep(0.6)
    process_l.start()

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        process_r.terminate()
        process_l.terminate()
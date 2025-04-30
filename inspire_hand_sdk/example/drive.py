from asyncio import SelectorEventLoop
import multiprocessing
import time
from inspire_sdkpy import inspire_sdk
import sys
import argparse

def worker(config, use_serial=True, include_touch=True, gui=True):
    try:
        if use_serial:
            handler=inspire_sdk.ModbusDataHandler(serial_port=config['serial_port'], LR=config['side'], device_id=config['device_id'], use_serial=True, include_touch=include_touch)
        else:
            handler=inspire_sdk.ModbusDataHandler(ip=config['ip'], LR=config['side'], device_id=config['device_id'],
            include_touch=include_touch)
    except Exception as e:
        print(f"Failed to connect to hand {config['side']}: {e}")
        return

    if gui:
        from inspire_sdkpy import qt_tabs
        app = qt_tabs.QApplication(sys.argv)
        window = qt_tabs.MainWindow(data_handler=handler, 
            dt=20, #50hz
            name=f"Hand {config['side']}", 
            run_time=False, 
            Plot_touch=include_touch
        )
        window.reflash()
        window.show()
        sys.exit(app.exec_())
    else:
        call_count = 0  # 记录调用次数
        start_time = time.perf_counter()  # 记录开始时间
        while True:
            data_dict = handler.read()
            # print(data_dict['touch']['fingerone_tip_touch'][0,0])
            time.sleep(0.001)
            call_count += 1  # 增加调用计数
            # 每秒计算并打印一次调用频率
            if call_count % 100 == 0:  # 每 100 次调用计算一次频率
                elapsed_time = time.perf_counter() - start_time  # 计算总耗时
                frequency = call_count / elapsed_time  # 计算频率 (Hz)
                print(f"当前频率: {frequency:.2f} Hz, 调用次数: {call_count}, 耗时: {elapsed_time:.6f} 秒")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Control Inspire Hand')
    parser.add_argument('--TCP', dest='use_serial', action='store_false',
                        help='Use TCP instead of serial communication')
    parser.add_argument('--no-touch', dest='include_touch', action='store_false',
                        help='Disable touch sensors')
    parser.add_argument('--no-gui', dest='gui', action='store_false',
                        help='Disable GUI')
    parser.set_defaults(use_serial=True, include_touch=True, gui=True)
    args = parser.parse_args()

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
    
    process_l = multiprocessing.Process(target=worker, args=(config['left'], args.use_serial, args.include_touch, args.gui))
    process_r = multiprocessing.Process(target=worker, args=(config['right'], args.use_serial, args.include_touch, args.gui))

    process_r.start()
    time.sleep(0.6)
    process_l.start()

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        process_r.terminate()
        process_l.terminate()

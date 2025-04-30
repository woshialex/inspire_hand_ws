import time
import sys
import threading
from unitree_sdk2py.core.channel import ChannelPublisher, ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.utils.thread import Thread

from inspire_sdkpy import inspire_hand_defaut,inspire_dds
import numpy as np
from copy import deepcopy

class InspireController():
    def __init__(self, network=None, include_touch=True, LR='r'):
        super().__init__()  # 调用父类的 __init__ 方法
        ChannelFactoryInitialize(0, network)

        self.pub_cmd = ChannelPublisher("rt/inspire_hand/ctrl/"+LR, inspire_dds.inspire_hand_ctrl)
        self.pub_cmd.Init()

        self.data_touch_lock = threading.Lock()
        self.data_state_lock = threading.Lock()
        self.sub_states = ChannelSubscriber("rt/inspire_hand/state/"+LR, inspire_dds.inspire_hand_state)
        self.sub_states.Init(self.update_data_state, 10)

        if include_touch:
            self.sub_touch = ChannelSubscriber("rt/inspire_hand/touch/"+LR, inspire_dds.inspire_hand_touch)
            self.sub_touch.Init(self.update_data_touch, 10)
        
        self._states={}
        self._touch={}
        self.cmd = inspire_hand_defaut.default_inspire_hand_ctrl()
        self.get_ready(max_force=300, max_speed=500)

        # self.cmd.mode
        # mode 0：0000（无操作）
        # mode 1：0001（角度）
        # mode 2：0010（位置）
        # mode 3：0011（角度 + 位置）
        # mode 4：0100（力控）
        # mode 5：0101（角度 + 力控）
        # mode 6：0110（位置 + 力控）
        # mode 7：0111（角度 + 位置 + 力控）
        # mode 8：1000（速度）
        # mode 9：1001（角度 + 速度）
        # mode 10：1010（位置 + 速度）
        # mode 11：1011（角度 + 位置 + 速度）
        # mode 12：1100（力控 + 速度）
        # mode 13：1101（角度 + 力控 + 速度）
        # mode 14：1110（位置 + 力控 + 速度）
        # mode 15：1111（角度 + 位置 + 力控 + 速度）  

    # 更新图形的函数
    def update_data_touch(self, msg:inspire_dds.inspire_hand_touch):
        with self.data_touch_lock:
            start_time = time.time()  # 记录开始时间
            for i, (name, addr, size,var) in enumerate(inspire_hand_defaut.touch_data_sheet):
                value=getattr(msg, var)
                matrix = np.array(value).reshape(size)
                self._touch[var]=matrix

            end_time = time.time()  # 记录结束时间
            elapsed_time = end_time - start_time  # 计算耗时
            # print(f"Data update time: {elapsed_time:.6f} seconds")  # 打印耗时
            
    def update_data_state(self, states_msg:inspire_dds.inspire_hand_state):
        with self.data_state_lock:
            self._states= {
                'POS_ACT': states_msg.pos_act,
                'ANGLE_ACT': states_msg.angle_act,
                'FORCE_ACT': states_msg.force_act,
                'CURRENT': states_msg.current,
                'ERROR': states_msg.err,
                'STATUS': states_msg.status,
                'TEMP': states_msg.temperature
            }

    def send_cmd(self, cmd:inspire_dds.inspire_hand_ctrl):
        self.pub_cmd.Write(cmd)

    def get_ready(self, max_force=100, max_speed=500):
        self.cmd.mode = 0b1101
        self.cmd.angle_set[:] = [1000] * 6
        self.cmd.speed_set[:] = [max_speed] * 6
        self.cmd.force_set[:] = [max_force] * 6 # weak force
        self.send_cmd(self.cmd)

    def open(self):
        self.cmd.mode = 0b0001
        self.cmd.angle_set[:] = [1000,1000,1000,1000,1000,0]
        self.send_cmd(self.cmd)

    def close(self):
        self.cmd.mode = 0b0001
        self.cmd.angle_set[:] = [0,0,0,0,0,0]
        self.send_cmd(self.cmd)
    
    def stop(self):
        self.cmd.mode = 0b0001
        # self.cmd.angle_set[:] = [-1] * 6
        self.cmd.angle_set[:] = self.state['ANGLE_ACT']
        self.send_cmd(self.cmd)

    def relax(self):
        self.cmd.mode = 0b1101
        # self.cmd.angle_set[:] = [-1] * 6 #can't send -1
        self.cmd.force_set[:] = [0] * 6
        self.send_cmd(self.cmd)

    @property
    def state(self):
        with self.data_state_lock:
            return deepcopy(self._states)

    @property
    def touch(self):
        with self.data_touch_lock:
            return deepcopy(self._touch)

if __name__ == '__main__':
    # cmd = inspire_hand_defaut.default_inspire_hand_ctrl()
    controller = InspireController(LR='r')
    controller.open()
    time.sleep(6.0)
    while True:
        controller.close()
        time.sleep(0.5)
    # controller.relax()
    # time.sleep(5.0)
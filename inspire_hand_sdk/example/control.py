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

        self.sub_states = ChannelSubscriber("rt/inspire_hand/state/"+LR, inspire_dds.inspire_hand_state)
        self.sub_states.Init(self.update_data_state, 10)

        if include_touch:
            self.sub_touch = ChannelSubscriber("rt/inspire_hand/touch/"+LR, inspire_dds.inspire_hand_touch)
            self.sub_touch.Init(self.update_data_touch, 10)
        
        self._states={}
        self._touch={}
        self.data_touch_lock = threading.Lock()
        self.data_state_lock = threading.Lock()

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

    @property
    def state(self):
        with self.data_state_lock:
            return deepcopy(self._states)

    @property
    def touch(self):
        with self.data_touch_lock:
            return deepcopy(self._touch)

if __name__ == '__main__':
    cmd = inspire_hand_defaut.default_inspire_hand_ctrl()
    controller = InspireController(LR='l')
    short_value=1000

    cmd.angle_set=[0,0,0,0,1000,1000]
    cmd.mode=0b0001
    controller.send_cmd(cmd)

    time.sleep(1.0)

    cmd.angle_set=[0,0,0,0,0,1000]
    cmd.mode=0b0001
    controller.send_cmd(cmd)

    time.sleep(1.0)

    for cnd in range(100000): 
        # 寄存器起始地址，0x05CE 对应的是 1486
        start_address = 1486            
        num_registers = 6  # 6 个寄存器
        # 生成要写入的值列表，每个寄存器为一个 short 值

        if (cnd+1) % 10 == 0:
            short_value = 1000-short_value  # 要写入的 short 值

        values_to_write = [short_value] * num_registers
        values_to_write[-1]=1000-values_to_write[-1]
        values_to_write[-2]=1000-values_to_write[-2]

        value_to_write_np=np.array(values_to_write)
        value_to_write_np=np.clip(value_to_write_np,200,800)
        # value_to_write_np[3]=800

        # 将组合模式按二进制方式实现
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
        cmd.angle_set=value_to_write_np.tolist()
        cmd.mode=0b0001
        #Publish message
        if  controller.send_cmd(cmd):
            # print("Publish success. msg:", cmd.crc)
            pass
        else:
            print("Waitting for subscriber.")

        time.sleep(0.1)
        

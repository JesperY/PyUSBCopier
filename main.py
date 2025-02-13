import socket
import wmi
import win32api

def monitor_usb():
    # 创建 WMI 对象，用于监控系统中的 USB 设备
    wmi_obj = wmi.WMI()

    # 创建 socket 连接，用于与服务器端通信
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # client_socket.connect(('127.0.0.1', 12345))

    # 获取当前所有 USB 设备的设备 ID
    last_usb_devices = get_usb_devices(wmi_obj)

    # 不断检测 USB 设备状态
    while True:
        # 获取当前所有 USB 设备的设备 ID
        current_usb_devices = get_usb_devices(wmi_obj)

        # 检测 U 盘插入和拔出事件
        message = detect_usb_change(last_usb_devices, current_usb_devices)
        # 如果检测到 U 盘插入或拔出，则向服务器端发送消息
        if message:
            print(message)
            # client_socket.send(message.encode())

        # 更新上一次检测的设备 ID
        last_usb_devices = current_usb_devices

        # 休眠一段时间，再进行下一次检测
        win32api.Sleep(1000)

    # 关闭 socket 连接
    client_socket.close()

def get_usb_devices(wmi_obj):
    # 获取当前所有 USB 设备的设备 ID
    usb_devices = wmi_obj.Win32_PnPEntity(ConfigManagerErrorCode=0)
    usb_device_ids = [device.DeviceID for device in usb_devices if 'USB' in device.PNPDeviceID]
    return usb_device_ids

def detect_usb_change(last_usb_devices, current_usb_devices):
    # 检测 U 盘插入和拔出事件
    message = ''
    for device in last_usb_devices:
        if device not in current_usb_devices:
            message = 'U盘已拔出'
            break
    for device in current_usb_devices:
        if device not in last_usb_devices:
            message = 'U盘已插入'
            break
    return message

if __name__ == '__main__':
    monitor_usb()
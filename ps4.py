import hid

add_buttons = [1, 2, 16, 32, 64, 128] # L1,R1,Share,Options,L3,R3
main_buttons = [2, 4, 6, 8, 24, 40, 72, 136] # up, right, down, left, empty, sq, x, o, tri

class PS4Controller():
    """DOC"""
    def button_parser(self, arr, value):
        btn_states = []
        for i in range(len(arr)):
            btn_states.append(0)

        temp = value
        for i in range(len(arr)):
            if (temp / arr[(len(arr) - 1) - i]) > 0 :
                temp -= int(arr[(len(arr) - 1) - i])
                btn_states[(len(arr) - i) - 1] = 1
        return btn_states

    def __init__(self, vendor, product):
        self.h = hid.device()
        self.h.open(vendor, product)
        self.h.set_nonblocking(1)
        self.raw_data = []
        self.h.get_feature_report(2, 100)
        self.angles_raw = [0., 0., 0.]
        self.gyro_raw = [0., 0., 0.]
        self.accel_raw = [0., 0., 0.]
        self.axis_raw = [0., 0., 0., 0., 0., 0.]
        self.button_raw = 0
        self.additional_buttons = 0
        self.battery_level = 0 # Digital
        self.battery = 0 # Float
        self.buttons = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        self.angles = [0., 0., 0.]
        self.gyro = [0., 0., 0.]
        self.accel = [0., 0., 0.]
        self.axis = [0., 0., 0., 0., 0., 0.]

    def update_raw(self):
        self.raw_data = self.h.read(128)
        if len(self.raw_data) > 75 and len(self.raw_data) <= 78:
            if self.raw_data[0] == 17 and self.raw_data[1] == 192:
                self.offset = 2
            else:
                self.offset = 0

            self.angles_raw[0] = self.raw_data[22 + self.offset] # Yaw
            self.angles_raw[1] = self.raw_data[24 + self.offset] # Pitch
            self.angles_raw[2] = self.raw_data[20 + self.offset] # Roll

            self.gyro_raw[0] = self.raw_data[21 + self.offset] # Yaw
            self.gyro_raw[1] = self.raw_data[23 + self.offset] # Pitch
            self.gyro_raw[2] = self.raw_data[19 + self.offset] # Roll

            self.accel_raw[0] = self.raw_data[13 + self.offset] # x
            self.accel_raw[1] = self.raw_data[15 + self.offset] # y
            self.accel_raw[2] = self.raw_data[17 + self.offset] # z

            self.axis_raw[0] = self.raw_data[1 + self.offset] # Left-x
            self.axis_raw[1] = self.raw_data[2 + self.offset] # Left-y
            self.axis_raw[2] = self.raw_data[3 + self.offset] # right-x
            self.axis_raw[3] = self.raw_data[4 + self.offset] # right-y
            self.axis_raw[4] = self.raw_data[8 + self.offset] # left-trigger
            self.axis_raw[5] = self.raw_data[9 + self.offset] # right-trigger

            self.button_raw = self.raw_data[5 + self.offset]
            self.additional_buttons = self.raw_data[6 + self.offset]
            self.battery_level = self.raw_data[30 + self.offset] * 10
            self.battery = self.raw_data[12 + self.offset]
            #self.battery *= float(100) / float(255)

    def angle_calibration(self):
        THRESHOLD = 150
        for i in range(3):
            if self.angles_raw[i] > THRESHOLD:
                self.angles[i] = self.angles_raw[i] - 255
            else:
                self.angles[i] = self.angles_raw[i]
            self.angles[i] *= 3

    def update(self):
        self.update_raw()
        self.angle_calibration()

t = PS4Controller(0x054C, 0x09CC)

while True:
    t.update()
    print t.battery_level
    # print t.button_parser(main_buttons, t.button_raw)
    # print t.button_parser(add_buttons, t.additional_buttons)
    # if len(t.raw_data) > 0: print t.raw_data
    # print t.additional_buttons
    # print t.angles

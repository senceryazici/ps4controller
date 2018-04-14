import hid
from time import sleep
from pymouse import PyMouse

add_buttons = [1, 2, 16, 32, 64, 128] # L1,R1,Share,Options,L3,R3
main_buttons = [2, 4, 6, 8, 24, 40, 72, 136] # up, right, down, left, empty, sq, x, o, tri
# TODO: FILTERS TO BE ADDED: KALMAN, COMPLEMENTARY FOR BOTH GYRO AND AXIS

class PS4Controller():
    """PS4 Controller HID Library"""

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
        self.m = PyMouse()
        self.angles = [0., 0., 0.]
        self.gyro = [0., 0., 0.]
        self.accel = [0., 0., 0.]
        self.axis = [0., 0., 0., 0., 0., 0.]

        # Mouse
        self.finger_old = [[0, 0, 0, 0], [0, 0, 0, 0]]
        self.finger = [[0, 0, 0, 0], [0, 0, 0, 0]]
        self.finger_max = [0, 0]
        self.touching_old = [False, False]
        self.last_erased = False
        self.count = 0

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

            # self.gyro_raw[0] = self.raw_data[21 + self.offset] # Yaw
            # self.gyro_raw[1] = self.raw_data[23 + self.offset] # Pitch
            # self.gyro_raw[2] = self.raw_data[19 + self.offset] # Roll
            self.gyro_raw[0] = self.raw_data[16 + self.offset] # Yaw
            self.gyro_raw[1] = self.raw_data[14 + self.offset] # Pitch
            self.gyro_raw[2] = self.raw_data[18 + self.offset] # Roll

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

            # NOTE: Battery Level has +-10% error, and is between 0-10. multiply by 10 to scaling it up to 0-100
            self.battery_level = self.raw_data[30 + self.offset] * 10

            # TODO: Floating Battery with precision needs to be discovered.
            self.battery = self.raw_data[12 + self.offset]


            self.finger[0][0] = self.raw_data[37 + self.offset] # X
            self.finger[0][1] = self.raw_data[38 + self.offset] # Y
            self.finger[0][2] = self.raw_data[36 + self.offset] # counter
            self.finger[0][3] = self.raw_data[35 + self.offset] # finger detector

    def angle_calibration(self):
        THRESHOLD = 150
        for i in range(3):
            if self.angles_raw[i] > THRESHOLD:
                self.angles[i] = self.angles_raw[i] - 255
            else:
                self.angles[i] = self.angles_raw[i]
            self.angles[i] *= 3


    def gyro_calibration(self):
            THRESHOLD = 150
            for i in range(3):
                if self.gyro_raw[i] > THRESHOLD:
                    self.gyro[i] = self.gyro_raw[i] - 255
                else:
                    self.gyro[i] = self.gyro_raw[i]
                self.gyro[i] *= 45.0 / 2.0

    def _button_parser(self, arr, value):
        btn_states = []
        for i in range(len(arr)):
            btn_states.append(0)

        temp = value
        for i in range(len(arr)):
            if (temp / arr[(len(arr) - 1) - i]) > 0 :
                temp -= int(arr[(len(arr) - 1) - i])
                btn_states[(len(arr) - i) - 1] = 1
        return btn_states

# FIXME: mouse event is BUGGY
    def move_mouse(self):
        if self.finger[0][3] > self.finger_max[0]:
            self.finger_max[0] = self.finger[0][3]

        if self.finger_max[0] - self.finger[0][3] > 100:
            self.touching_old[0] = True
            K = 1
            v = 0.
            # print self.finger[0][2]
            # print self.finger_old[0][2]
            # print ""

            if (self.finger[0][2] - self.finger_old[0][2]) != 0:
                v = K * float(self.finger[0][1] - self.finger_old[0][1]) #
            if v != 0:
                print v
            # if v >= 0:
            #     v = v * v / K
            # else:
            #     v = -1 * v * v / 10
            if self.last_erased:
                v = 0
                self.last_erased = False
            oldposx, oldposy = self.m.position()
            self.m.move(oldposx, oldposy + v)
            if self.count % 1 == 0:
                self.finger_old[0] = list(self.finger[0])
        else:
            if self.touching_old[0]:
                print "ERASING"
                self.last_erased = True
                print self.finger[0][1]
                print self.finger_old[0][1]
                self.finger_old[0] = list(self.finger[0])
            self.touching_old[0] = False


    def update(self):
        self.update_raw()
        self.angle_calibration()
        self.gyro_calibration()
        self.move_mouse()

        self.count += 1
        if self.count >= 10000:
            self.count = 0

t = PS4Controller(0x054C, 0x09CC)
a = 0
while True:
    t.update()
    a += t.gyro[2] * 0.001
    # print str(t.gyro) + "\t" + str(a)
    sleep(0.001)
    # TEMP: This section is for debugging!

    # FIXME: Main buttons HID input does not work as additional buttons. Their algorithm is different.
    # print t._button_parser(main_buttons, t.button_raw)

    # print t._button_parser(add_buttons, t.additional_buttons)

from pylablib.devices import Thorlabs

SCALE_FACTOR = 2.9E-5

class StageController:
    def __init__(self, serial):
        # i = 1 # do something
        print("Initialising stage", serial)
        self.serial = serial
        self.stage = Thorlabs.KinesisMotor(serial)
        # self.stage.home()

    def setup_velocity(self, min_velocity, acceleration, max_velocity):
        min_velocity_scaled = min_velocity / SCALE_FACTOR
        acceleration_scaled = acceleration / SCALE_FACTOR
        max_velocity_scaled = max_velocity / SCALE_FACTOR
        self.stage.setup_velocity(min_velocity=min_velocity_scaled, acceleration=acceleration_scaled, max_velocity=max_velocity_scaled, scale=True)
    
    def move_by(self, distance):
        distance_scaled = distance / SCALE_FACTOR
        print("Stage", self.serial, "moving by", distance, "mm")
        self.stage.move_by(distance_scaled, scale=True)

    def stop(self):
        self.stage.stop()

    def home(self):
        print("Stage", self.serial, "moving to home")
        self.stage.home()

    def is_moving(self):
        return self.stage.is_moving()
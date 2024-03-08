from tasks.imu import Task as imu
from tasks.monitor import Task as monitor



TASK_REGISTRY = {
    "IMU": imu,
    "MONITOR": monitor
}

TASK_MAPPING_ID = {
    "MONITOR": 0x00,
    "IMU": 0x01
}


SM_CONFIGURATION = {
    "STARTUP": {
        "Tasks": {
            "MONITOR": {
                "Frequency": 1,
                "Priority": 2,
                "ScheduleLater": False
            }
        },
        "MovesTo": [
            "NOMINAL",
        ]
    },
    "NOMINAL": {
        "Tasks": {
            "MONITOR": {
                "Frequency": 5,
                "Priority": 2,
                "ScheduleLater": False
            },
            "IMU": {
                "Frequency": 1,
                "Priority": 3,
                "ScheduleLater": False
            }
        },
        "MovesTo": [
            "SAFE",
        ]
    },
    "SAFE": {
        "Tasks": {
            "Monitor": {
                "Frequency": 20,
                "Priority": 1,
                "ScheduleLater": False
            },
            "IMU": {
                "Frequency": 2,
                "Priority": 3,
                "ScheduleLater": False
            }
        },
        "MovesTo": [
            "NOMINAL"
        ],
        "Enters": [
            "print"
        ],
        "Exit": [
            "print"
        ]
    }
}

initial = None

# Note, dangerous to put code here as evverything will run on import
# Ideally, switch to another configuration format

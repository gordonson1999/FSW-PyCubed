from tasks.imu import Task as imu
from tasks.monitor import Task as monitor
from tasks.timing import Task as timing
from tasks.obdh import Task as obdh


TASK_REGISTRY = {
    "MONITOR": monitor,
    "TIMING": timing,
    "OBDH": obdh,
    "IMU": imu
    
}

TASK_MAPPING_ID = {
    "MONITOR": 0x00,
    "TIMING": 0x01,
    "OBDH": 0x02,
    "IMU": 0x03
}


SM_CONFIGURATION = {
    "STARTUP": {
        "Tasks": {

            "MONITOR": {
                "Frequency": 1,
                "Priority": 1,
                "ScheduleLater": False
            },

            "TIMING": {
                "Frequency": 1,
                "Priority": 2,
                "ScheduleLater": False
            },

            "OBDH": {
                "Frequency": 0.25,
                "Priority": 3,
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
                "Frequency": 2,
                "Priority": 2,
                "ScheduleLater": False
            },

            "TIMING": {
                "Frequency": 1.5,
                "Priority": 2,
                "ScheduleLater": False
            },

            "OBDH": {
                "Frequency": 1,
                "Priority": 3,
                "ScheduleLater": False
            },
            
            "IMU": {
                "Frequency": 1,
                "Priority": 5,
                "ScheduleLater": True
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

# Note: Ideally, switch to another configuration format. Don't want things to run on import


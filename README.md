# DTK WNPR app

The wagon number recognition application is based on [DTK software](https://www.dtksoft.com/wnrsdk)

**Functionality**:

1) Detect, Track and Recognizer wagon numbers
2) Ability to determine the direction of movement
3) Ability to control sending wagon numbers through counting the number of times to generate an event

## Installation
1) Download from here [SDK](https://www.dtksoft.com/downloads)
2) DTKWNRSDK_Trial/lib/linux/x86_64 move files to /usr/lib directory
3) To run the code, use sudo together

Clone the repo
```bash
git clone https://gitlab.com/parquor/parqourcv/parking_py.git
```

Use the package manager pip to install requirements.

```bash
pip install -r requirements
```

## Usage

Read [SDK Documentation](https://www.dtksoft.com/docs/wnrsdk/) \
When starting the code, specify the ip of the camera and the ip of the server
```python3.11
sudo python main.py -ip camera_ip -server server_ip
```
 
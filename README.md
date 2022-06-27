# butler
This is a utility repository for organized data storage without the need to modify the original code.

The crux of this project is the `@butler` decorator. Simply decorate a function and it saves variables and print outputs as you like.


### Data measured @CTU KN:E-210
- https://drive.google.com/drive/folders/127ytcRVTQYGDsdSTxj3F47wPl_egFChO?usp=sharing

## TODO
- tutorial on how to use it to:
  - record experiments
  - upload dictionaries
- add examples
- add a link to this repository on the website https://ptak.felk.cvut.cz/ipalm

## how to use
- inside the decorated function set the variables that you want to be saved as `butler.meas_object_to_be_saved = etc` & `butler.meas_setup = etc2`
- if the decorated function is a class function, then the variables of the class can also be accessed. See the example
- a `setup.json` file has to be present in the top directory where the experiment data is going to be saved

### example
```
class MeasObject:
    def __init__(self, meas_prop, meas_type, params, values, units, meas_ID):
        self.meas_prop = meas_prop  # eg mass, elasticity, vision, sound
        self.meas_type = meas_type  # continuous, discrete
        self.params = params  #
        self.values = values
        self.units = units
        self.meas_ID = meas_ID
        

class TestClass:
    def __init__(self):
        self.test_value1 = {"gripper_name": {"position": [1, 2, 3, 4, 5, 6, 7, 8, 9]}}
        self.test_value2 = {"gripper_name": {"values": [9, 8, 7, 6, 5, 6, 7, 8, 9]}}
        self.test_value3 = {"arm_name": {"current": [1, 2, 3, 4, 5, 6, 7, 8, 9]}}
        self.test_value4 = {"camera": {"point_cloud": "pointcloud.png"}}
        self.data_variables = {}

    @Butler(keywords="[INFO]", keep_keywords=False, data_variables=("self.data_variables", ),
            create_new_exp_on_run=True, setup_file=r"../setup.json")
    def divide(self, a, b):
        _meas = PropertyMeasurement(meas_prop="object_category",
                                    meas_type="continuous",  # "categorical",
                                    params={"mean": 20.2, "std": 5.1, "units": "kg", "name": "x"},
                                    meas_ID=6)
        print("this is in the top log")
        print("[INFO] this is in the property log")

        Butler.add_object_context({"common_name": "ycb_cup", "dataset_id": "65-f_cup", "dataset": "ycb", "maker": "sample_company"})
        for k in self.test_value4:
            self.data_variables[k] = self.test_value4[k]
        for k in self.test_value1:
            self.data_variables[k] = self.test_value1[k]
        Butler.add_tmp_files(r"../unused/tests/setup_cropped.png", "data", "pointcloud.png")
        Butler.add_measurement_png(r"../unused/tests/setup_cropped.png")

        _meas.gripper_pose = {"position": [0.1, 0.2, 0.3], "rotation": [0.5, 0.8, 3.14], "grasped": True}
        _meas.object_pose = {"position": [0.3, 0.2, 0.1], "rotation": [3.0, 0.8, 3.14]}
        return _meas, a / b

bc = TestClass()
d = bc.divide(40, 20)

```

# sphinx documentation
- commands in `docs/` folder:
  - `sphinx-apidoc -o ./source ..` - creates modules for all files
  - `.\make.bat html` - makes the html
  - `.\make.bat json` - makes the json version of it
- [basic tree tutorial](https://eikonomega.medium.com/getting-started-with-sphinx-autodoc-part-1-2cebbbca5365)
  - above `.. toctree::` in `docs/source/index.rst`:
    - ```
      .. automodule:: butler2
      :members:
      ```
- [modules tutorial](https://www.youtube.com/watch?v=b4iFyrLQQh4) (better atm)
  - below `.. toctree::` in `docs/source/index.rst`:
    - ```
      **[empty line]**
      modules
      ```


# difference between ROSBAG & this
- rosbags need the actual *datatype + ROS*
- this is just *json + internet*

# 05/20
- final fixes

# 05/03
- add lazy post measurements

# 04/30
- test uploading with as broken data as possible
- check which requirements are necessary

# 04/28
- TODO: add **grasp and object pose** to kinova setup outputs to butler

# 04/25
- TODO: add the possibility to read sensor data from the MeasObject json as opposed to only reading it from extra JSONs per setup element

### 04/23
- add timestamp in names
- add docs
- fix file inconsistencies when setting tmp files
  - now it's possible to just enter

### 04/19
- Jan tips:
  - button triggers at runtime - e.g. when you press 'x', save the timestamp
  - maybe experiment_timestamp
  - UUID for timestamps

### 04/16
- add `uploader.py`
  - this tests uploading to the server using the formatted json *and* with files in the request

### 04/15
- somewhat done file saving:
  - measurement["png"], object\_instance["other\_file"], measurement["sensor"]["quantity"] 

### 04/12
- add `norach.py` - this will upload the processed measurements to the django rest endpoint

### 04/04-05
- make steward
  - done: continuous property class processing
  - todo: categorical property class processing
  - todo: generalize `PropertyMeasurement` class so it also fits andrej's class - in addition to `.parameters` also `.params` and all these shortcuts

### 04/03
- made butler into a static class
- TODO: context setting & getting

### TODO
- make butler a class with a function called butler, then:
```
class Butler:
    static_fields_only
    etc
    
    @classmethod
    def butler(cls, etc):
        etc
        def wrapper(etc):
            def inner_func(etc):
                etc
                return etc
            etc
            return etc
        etc
        return etc

butler = Butler.butler  # this dude can then have field so that the IDE recognizes them
```




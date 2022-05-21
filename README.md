# butler
This is a utility repository for organized data storage without the need to modify the original code.

The crux of this project is the `@butler` decorator. Simply decorate a function and it saves variables and print outputs as you like.


### Data measured @CTU KN:E-210
- https://drive.google.com/drive/folders/127ytcRVTQYGDsdSTxj3F47wPl_egFChO?usp=sharing



## how to use
- inside the decorated function set the variables that you want to be saved as `butler.meas_object_to_be_saved = etc` & `butler.meas_setup = etc2`
- if the decorated function is a class function, then the variables of the class can also be accessed. See the example
- a `setup.json` file has to be present in the top directory where the experiment data is going to be saved

### example
```
    @butler.Butler(keywords=['[BUTLER-TEST]', '[INFO]', '[INFER-INFO]', '[INFER]', '[ACSEL]', '[ACSEL-INFO]'],
                   setup_file="/home/robot3/vision_ws/src/ipalm_control/butler/setup.json",
                   data_variables=("self.data_variables", ))
    def exploratoryAction(self, planned_action, mod_specs, translation_pos, mes_rot, iteration, ID):

        assert isinstance(mod_specs, ut.model_specs)
        _meas = None
        self.camera1_values["camera"]["image"] = ""
        self.gripper_values["gripper"] = {}
        self.arm_values["arm"]["joint4_torque"] = []
        self.camera1_values["camera"]["image"] = ""
        self.microphone_values["microphone"]["recording"] = ""
        self.gripper_position = translation_pos
        self.gripper_rotation = mes_rot
        
        # ... shortened for this example
        self.data_variables = butler.format_data_variables((self.microphone_values, self.arm_values, self.gripper_values, self.camera1_values))
        current_object_dataset_id = None
        current_common_name = "soft_yellow_sponge"
        current_dataset = None
        
        if current_object_dataset_id in object_position_dict:
            self.object_rotation, self.object_position = object_position_dict[current_object_dataset_id]
        if current_common_name in object_position_dict:
            self.object_rotation, self.object_position = object_position_dict[current_common_name]

        _meas.object_pose = {"rotation": self.object_rotation, "position": self.object_position}
        _meas.gripper_pose = {"rotation": self.gripper_rotation, "position": self.gripper_position, "grasped": self.gripper_has_grasped}
        butler.Butler.add_object_context({"common_name": current_common_name, "dataset_id": current_object_dataset_id, "dataset": current_dataset})
        return _meas, mod_specs

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




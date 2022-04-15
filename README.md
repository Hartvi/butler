# butler
This is a utility repository for organized data storage without the need to modify the original code.

The crux of this project is the `@butler` decorator. Simply decorate a function and it saves variables and print outputs as you like.

### 04/15
- somewhat done file saving:
  - measurement["png"], object\_instance["other\_file"], measurement["sensor"]["quantity"] 

### 04/12
- add `norach.py` - this will upload the processed measurements to the django rest endpoint

### 04/04-05
- make steward
  - done: continuous property class processing
  - todo: categorical property class processing
  - todo: generalize `PropertyMeasurement` class so it also fits andrej's class - in addition to `.parameters` also `.params` and all those shortcuts

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

## how to use
- inside the decorated function set the variables that you want to be saved as `butler.meas_object_to_be_saved = etc` & `butler.meas_setup = etc2`
- if the decorated function is a class function, then the variables of the class can also be accessed. See the example
- a `setup.json` file has to be present in the top directory where the experiment data is going to be saved


### example
```
class BullshitClass:
    def __init__(self):
        self.bullshit_value = [1,2,3,4,5,6,7,8,9]

    @butler("[INFO]", delimiter="\n", data_variables=("self.bullshit_value", ))
    def multiply(self, a, b):
        _meas = MeasObject("youngs_modulus", "continuous", {"mean": 500000, "std": 100000}, [1,5,8,5,2,7,5,1,3,8,7,1,5,8,85,1,5,8,8,4,12,65], 6)
        print("this should only be in the top log")
        print("[INFO] no thanks")
        print("result: ", a*b)
        # print(dir())
        return _meas, a*b

```


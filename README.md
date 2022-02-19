# butler
This is a utility repository for organized data storage without the need to modify the original code.

The crux of this project is the `@butler` decorator. Simply decorate a function and it saves variables and print outputs as you like.


## how to use
- inside the decorated function set the variables that you want to be saved as `butler.meas_object_to_be_saved = etc` & `butler.meas_setup = etc2`


### example
```
@butler("[INFO]", delimiter="\n", keep_prints=False, meas_object_var_name="andrej_meas", meas_setup="andrej_setup")
def multiply(a, b):
    # print(andrej_meas)
    butler.andrej_setup = {"gripper": "2F85", "manipulator": "kinova lite 2"}
    butler.andrej_meas = MeasObject("andrejprop", "andrej", "andrej2", "andrej3", 6549547974)
    print("this should only be in the top log")
    print("[INFO] no thanks")
    print("result: ", a*b)
    return a*b

```


import numpy as np
from typing import List, Union, Tuple


class ClassWUnits:
    units: List[str] = list()
    unit2id = dict()

    def __init__(self, val: float, units: Union[str, np.ndarray] = None):
        self.val = val
        if type(units) == str:
            if units not in ClassWUnits.unit2id:
                ClassWUnits.unit2id[units] = len(ClassWUnits.units)
                ClassWUnits.units.append(units)
            self.unit_list = np.array([0] * len(ClassWUnits.units))
            self.unit_list[ClassWUnits.unit2id[units]] = 1
        else:  # units: np.ndarray
            assert len(units) <= len(ClassWUnits.units), "Trying to assign units that do not exist. Unit list too long!"
            self.unit_list = units

    def __mul__(self, other):
        if type(other) == ClassWUnits:
            return ClassWUnits(other.val * self.val, self.add_units(other))
        else:  # float/int/etc
            return ClassWUnits(other * self.val, self.unit_list)

    def __rmul__(self, other):
        if type(other) == ClassWUnits:
            return ClassWUnits(other.val * self.val, self.add_units(other))
        else:  # float/int/etc
            if other == 0 or other == 0.0:
                return 0.0
            return ClassWUnits(other * self.val, self.unit_list)

    def __add__(self, other):
        # assert type(other) == ClassWUnits, "ClassWUnits can only be added to other instances of ClassWUnits"
        assert other.unit_list == self.unit_list, "Units must agree"
        return ClassWUnits(other.val + self.val, self.unit_list)

    def __radd__(self, other):
        # assert type(other) == ClassWUnits, "ClassWUnits can only be added to other instances of ClassWUnits"
        assert other.unit_list == self.unit_list, "Units must agree"
        return ClassWUnits(other.val + self.val, self.unit_list)

    def __repr__(self):
        unit_str = ""
        for i in range(len(self.unit_list)):
            unit_str += ClassWUnits.units[i]
            unit_str += f"^{self.unit_list[i]}" if (self.unit_list[i] > 1 or self.unit_list[i] < 0) else ""
            unit_str += " "
        return str(self.val) + " " + unit_str

    def add_units(self, other):
        leno = len(other.unit_list)
        lens = len(self.unit_list)
        extended_units = np.zeros(np.max([leno, lens]), dtype=int)
        extended_units[:lens] = self.unit_list
        extended_units[:leno] += other.unit_list
        return extended_units


if __name__ == "__main__":
    a = ClassWUnits(2.0, "m")
    b = ClassWUnits(3.0, "s")
    print(a*b*a*b)
    print((a*b*a*b).unit_list)
    print(a.unit_list)
    print(b.unit_list)




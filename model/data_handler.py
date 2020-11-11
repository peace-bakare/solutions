""" Super class to contain and manage data """
import pandas as pd
import numpy as np

class DataHandler:

    def clean_nan(dataframe):
        for year in dataframe.keys():
            if (np.isnan(dataframe[year])):
                dataframe[year] = 0.0
        return dataframe

    def to_json(self, clean_nan=clean_nan):
        var_keys = vars(self).keys()
        outputs = dict()
        obj_vars = dir(self)
        for k in obj_vars:
            func = getattr(self, k)
            if hasattr(func, 'wrapped'):
                outputs[k] = clean_nan(func())
        return outputs

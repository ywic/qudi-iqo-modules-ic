# -*- coding: utf-8 -*-
"""
This file contains methods for decay-like fitting, these methods
are imported by class FitLogic.

Qudi is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Qudi is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Qudi. If not, see <http://www.gnu.org/licenses/>.

Copyright (c) the Qudi Developers. See the COPYRIGHT.txt file at the
top-level directory of this distribution and at <https://github.com/Ulm-IQO/qudi/>
"""


import logging
logger = logging.getLogger(__name__)
import numpy as np
from lmfit.models import Model
from lmfit import Parameters

############################################################################
#                                                                          #
#               bare stretched exponential decay                           #
#                                                                          #
############################################################################

def make_barestretchedexponentialdecay_model(self, prefix=None):
    """ Create a general bare exponential decay model.

    @param str prefix: optional string, which serves as a prefix for all
                       parameters used in this model. That will prevent
                       name collisions if this model is used in a composite
                       way.

    @return tuple: (object model, object params)

    Explanation of the objects:
        object lmfit.model.CompositeModel model:
            A model the lmfit module will use for that fit. Here a
            gaussian model. Returns an object of the class
            lmfit.model.CompositeModel.

        object lmfit.parameter.Parameters params:
            It is basically an OrderedDict, so a dictionary, with keys
            denoting the parameters as string names and values which are
            lmfit.parameter.Parameter (without s) objects, keeping the
            information about the current value.

    """
    def barestretchedexponentialdecay_function(x, beta, lifetime):
        """ Function of a bare exponential decay.

        @param array x: variable variable - e.g. time
        @param float lifetime: lifetime

        @return: bare exponential decay function: in order to use it as a model
        """
        return np.exp(-np.power(x/lifetime, beta))

    model = Model(barestretchedexponentialdecay_function, independent_vars='x',
                  prefix=prefix)
    params = model.make_params()

    return model, params

############################################################################
#                                                                          #
#                  bare single exponential decay                           #
#                                                                          #
############################################################################


def make_bareexponentialdecay_model(self, prefix=None):
    """ Create a bare single exponential decay model.

    @param str prefix: optional string, which serves as a prefix for all
                       parameters used in this model. That will prevent
                       name collisions if this model is used in a composite
                       way.

    @return tuple: (object model, object params)

    Explanation of the objects:
        object lmfit.model.CompositeModel model:
            A model the lmfit module will use for that fit. Here a
            gaussian model. Returns an object of the class
            lmfit.model.CompositeModel.

        object lmfit.parameter.Parameters params:
            It is basically an OrderedDict, so a dictionary, with keys
            denoting the parameters as string names and values which are
            lmfit.parameter.Parameter (without s) objects, keeping the
            information about the current value.

    """

    bare_exp_decay, params = self.make_barestretchedexponentialdecay_model(prefix=prefix)

    bare_exp_decay.set_param_hint(name='beta', value=1, vary=False)
    params = bare_exp_decay.make_params()

    return bare_exp_decay, params


def estimate_bareexponentialdecay(self, x_axis, data, params):
    """ Provide an estimation for initial values for a bare exponential decay.

    @param numpy.array x_axis: x values
    @param numpy.array data: value of each data point corresponding to x values
    @param lmfit.Parameters params: object includes parameter dictionary which
                                    can be set

    @return tuple (error, params):

    Explanation of the return parameter:
        int error: error code (0:OK, -1:error)
        Parameters object params: set parameters of initial values
    """

    error = self._check_1D_input(x_axis=x_axis, data=data, params=params)

    # remove all the data that can be smaller than or equals to data.std()
    # when the data is smaller than std of the data, it is beyond the resolution
    # which is not helpful to our fitting.
    for i in range(0, len(x_axis)):
        if data[i] <= data.std():
            break

    # take the logarithm of data, calculate the life time with linear fit.
    data_log = np.log(data)

    minimum = 2 * (x_axis[1]-x_axis[0])

    try:
        linear_result = self.make_linear_fit(axis=x_axis[0:i],
                                             data=data_log[0:i],
                                             add_parameters=None)

        params['lifetime'].set(value=-1/linear_result.params['slope'].value, min=minimum)

    except:
        params['lifetime'].set(value=x_axis[i]-x_axis[0], min=minimum)
        logger.error('Linear fit did not work in estimate_bareexponentialdecay.')

    return error, params

def make_bareexponentialdecay_fit(self, x_axis, data, add_parameters=None):
    """ Perform a fit for the bare exponential on the provided data.

    @param numpy.array x_axis: 1D axis values
    @param numpy.array data: 1D data, should have the same dimension as x_axis.
    @param dict add_parameters: Additional parameters for the fit

    @return object result: lmfit.model.ModelFit object, all parameters
                           provided about the fitting, like: success,
                           initial fitting values, best fitting values, data
                           with best fit with given axis,...
    """
    bareexponentialdecay, params = self.make_bareexponentialdecay_model()

    error, params = self.estimate_bareexponentialdecay(x_axis, data, params)

    if add_parameters is not None:
        params = self._substitute_parameter(parameters=params,
                                            update_dict=add_parameters)
    try:
        result = bareexponentialdecay.fit(data, x=x_axis, params=params)
    except:
        result = bareexponentialdecay.fit(data, x=x_axis, params=params)
        logger.warning('The bare exponential decay fit did not work. lmfit '
                'result message: {}'.format(str(result.message)))
    return result

############################################################################
#                                                                          #
#                       single exponential decay                           #
#                                                                          #
############################################################################


def make_exponentialdecay_model(self, prefix=None):
    """ Create a exponential decay model with an amplitude.

    @param str prefix: optional string, which serves as a prefix for all
                       parameters used in this model. That will prevent
                       name collisions if this model is used in a composite
                       way.

    @return tuple: (object model, object params)

    Explanation of the objects:
        object lmfit.model.CompositeModel model:
            A model the lmfit module will use for that fit. Here a
            gaussian model. Returns an object of the class
            lmfit.model.CompositeModel.

        object lmfit.parameter.Parameters params:
            It is basically an OrderedDict, so a dictionary, with keys
            denoting the parameters as string names and values which are
            lmfit.parameter.Parameter (without s) objects, keeping the
            information about the current value.
    """

    amplitude_model, params = self.make_amplitude_model(prefix=prefix)
    bare_exp_model, params = self.make_bareexponentialdecay_model(prefix=prefix)

    exponentialdecay_model = amplitude_model*bare_exp_model
    params = exponentialdecay_model.make_params()

    return exponentialdecay_model, params


def estimate_exponentialdecay(self, x_axis, data, params):
    """ Provide an estimation for initial values for an exponential decay.

    @param numpy.array x_axis: x values
    @param numpy.array data: value of each data point corresponding to x values
    @param lmfit.Parameters params: object includes parameter dictionary which
                                    can be set

    @return tuple (error, params):

    Explanation of the return parameter:
        int error: error code (0:OK, -1:error)
        Parameters object params: set parameters of initial values
    """

    error = self._check_1D_input(x_axis=x_axis, data=data, params=params)

    # remove all the data that can be smaller than or equals to data.std()
    # when the data is smaller than std of the data, it is beyond the resolution
    # which is not helpful to our fitting.
    for i in range(0, len(x_axis)):
        if data[i] <= data.std():
            break

    # take the logarithm of data, calculate the life time with linear fit.
    data_log = np.log(data)

    minimum = 2 * (x_axis[1]-x_axis[0])

    try:
        linear_result = self.make_linear_fit(axis=x_axis[0:i],
                                             data=data_log[0:i],
                                             add_parameters=None)

        params['lifetime'].set(value=-1/linear_result.params['slope'].value,
                               min=minimum)
        params['amplitude'].set(value=linear_result.params['offset'].value)

    except:
        params['lifetime'].set(value=x_axis[i]-x_axis[0], min=minimum)
        logger.error('Linear fit did not work in estimate_exponentialdecay.')

    return error, params

def make_exponentialdecay_fit(self, x_axis, data, add_parameters=None):
    """ Perform a fit for the exponential on the provided data.

    @param numpy.array x_axis: 1D axis values
    @param numpy.array data: 1D data, should have the same dimension as x_axis.
    @param dict add_parameters: Additional parameters for the fit

    @return object result: lmfit.model.ModelFit object, all parameters
                           provided about the fitting, like: success,
                           initial fitting values, best fitting values, data
                           with best fit with given axis,...
    """
    exponentialdecay, params = self.make_exponentialdecay_model()

    error, params = self.estimate_exponentialdecay(x_axis, data, params)

    if add_parameters is not None:
        params = self._substitute_parameter(parameters=params,
                                            update_dict=add_parameters)
    try:
        result = exponentialdecay.fit(data, x=x_axis, params=params)
    except:
        result = exponentialdecay.fit(data, x=x_axis, params=params)
        logger.warning('The exponential decay fit did not work. lmfit '
                        'result message: {}'.format(str(result.message)))
    return result


############################################################################
#                                                                          #
#                single exponential decay with offset                      #
#                                                                          #
############################################################################


def make_exponentialdecayoffset_model(self, prefix=None):
    """ Create a exponential decay model with an amplitude and offset.

    @param str prefix: optional string, which serves as a prefix for all
                       parameters used in this model. That will prevent
                       name collisions if this model is used in a composite
                       way.

    @return tuple: (object model, object params)

    Explanation of the objects:
        object lmfit.model.CompositeModel model:
            A model the lmfit module will use for that fit. Here a
            gaussian model. Returns an object of the class
            lmfit.model.CompositeModel.

        object lmfit.parameter.Parameters params:
            It is basically an OrderedDict, so a dictionary, with keys
            denoting the parameters as string names and values which are
            lmfit.parameter.Parameter (without s) objects, keeping the
            information about the current value.
    """

    exp_decay_model, params = self.make_exponentialdecay_model(prefix=prefix)
    constant_model, params = self.make_constant_model(prefix=prefix)

    exp_decay_offset_model = exp_decay_model + constant_model
    params = exp_decay_offset_model.make_params()

    return exp_decay_offset_model, params

def estimate_exponentialdecayoffset(self, x_axis, data, params):
    """ Estimation of the initial values for an exponential decay function.

    @param numpy.array x_axis: 1D axis values
    @param numpy.array data: 1D data, should have the same dimension as x_axis.
    @param lmfit.Parameters params: object includes parameter dictionary which
                                    can be set

    @return tuple (error, params):

    Explanation of the return parameter:
        int error: error code (0:OK, -1:error)
        Parameters object params: set parameters of initial values
    """

    error = self._check_1D_input(x_axis=x_axis, data=data, params=params)

    # calculation of offset, take the last 10% from the end of the data
    # and perform the mean from those.
    offset = data[-max(1, int(len(x_axis)/10)):].mean()

    # substraction of offset, check whether
    if data[0] < data[-1]:
        data_level = offset - data
    else:
        data_level = data - offset

    # check if the data level contain still negative values and correct
    # the data level therefore. Otherwise problems in the logarithm appear.
    if data_level.min() <= 0:
        data_level = data_level - data_level.min()

    # remove all the data that can be smaller than or equals to std.
    # when the data is smaller than std, it is beyond resolution
    # which is not helpful to our fitting.
    for i in range(0, len(x_axis)):
        if data_level[i] <= data_level.std():
            break

    # values and bound of parameter.
    ampl = data[-max(1, int(len(x_axis) / 10)):].std()
    min_lifetime = 2 * (x_axis[1]-x_axis[0])

    try:
        data_level_log = np.log(data_level[0:i])

        # linear fit, see linearmethods.py
        linear_result = self.make_linear_fit(axis=x_axis[0:i],
                                             data=data_level_log,
                                             add_parameters=None)
        params['lifetime'].set(value=-1/linear_result.params['slope'].value,
                               min=min_lifetime)

        # amplitude can be positive of negative
        if data[0] < data[-1]:
            params['amplitude'].set(value=-np.exp(linear_result.params['offset'].value),
                                    max=-ampl)
        else:
            params['amplitude'].set(value=np.exp(linear_result.params['offset'].value),
                                    min=ampl)
    except:
        logger.error('Lifetime too small in estimate_exponentialdecayoffset, '
                     'beyond resolution!')

        params['lifetime'].set(value=x_axis[i]-x_axis[0],
                               min=min_lifetime)
        params['amplitude'].set(value=data_level[0])

    params['offset'].set(value=offset)

    return error, params


def make_exponentialdecayoffset_fit(self, x_axis, data, add_parameters=None):
    """
    This method performes a exponential decay fit on the provided data.

    @param numpy.array x_axis: 1D axis values
    @param numpy.array data: 1D data, should have the same dimension as x_axis.
    @param dict add_parameters: Additional parameters

    @return object result: lmfit.model.ModelFit object, all parameters
                           provided about the fitting, like: success,
                           initial fitting values, best fitting values, data
                           with best fit with given axis,...
    """
    exponentialdecay, params = self.make_exponentialdecayoffset_model()

    error, params = self.estimate_exponentialdecayoffset(x_axis, data, params)

    if add_parameters is not None:
        params = self._substitute_parameter(parameters=params,
                                            update_dict=add_parameters)
    try:
        result = exponentialdecay.fit(data, x=x_axis, params=params)
    except:
        result = exponentialdecay.fit(data, x=x_axis, params=params)
        logger.warning('The exponentialdecay with offset fit did not work. '
                       'Message: {}'.format(str(result.message)))
    return result

############################################################################
#                                                                          #
#                  bare double exponential decay                           #
#                                                                          #
############################################################################

def make_baredoubleexponentialdecay_model(self, prefix=None):
    """ Create a bare double exponential decay model.

    @param str prefix: optional string, which serves as a prefix for all
                       parameters used in this model. That will prevent
                       name collisions if this model is used in a composite
                       way.

    @return tuple: (object model, object params)

    Explanation of the objects:
        object lmfit.model.CompositeModel model:
            A model the lmfit module will use for that fit. Here a
            gaussian model. Returns an object of the class
            lmfit.model.CompositeModel.

        object lmfit.parameter.Parameters params:
            It is basically an OrderedDict, so a dictionary, with keys
            denoting the parameters as string names and values which are
            lmfit.parameter.Parameter (without s) objects, keeping the
            information about the current value.
    """

    bare_double_exp_decay, params = self.make_barestretchedexponentialdecay_model(prefix=prefix)

    bare_double_exp_decay.set_param_hint(name='beta', value=2, vary=False)
    params = bare_double_exp_decay.make_params()

    return bare_double_exp_decay, params


def estimate_baredoubleexponentialdecay(self, x_axis, data, params):
    """ Estimation of the initial values for an double exponential decay function.

    @param numpy.array x_axis: 1D axis values
    @param numpy.array data: 1D data, should have the same dimension as x_axis.
    @param lmfit.Parameters params: object includes parameter dictionary which
                                    can be set

    @return tuple (error, params):

    Explanation of the return parameter:
        int error: error code (0:OK, -1:error)
        Parameters object params: set parameters of initial values
    """
    error = self._check_1D_input(x_axis=x_axis, data=data, params=params)

    if data.min() < 0.0:
        error = -1
        logger.error('Data contains values which are below 0. \n'
                     'Estimate_baredoubleexponentialdecay failed. Try to use '
                     'estimate_doubleexponentialdecayoffset.')
        return error, params


    log_data = np.log(data)

    # At least 80% must be negative to be counted as an -(x/T)^2 decay.
    # Otherwise a (x/T)^2 decay is assumed.

    average_bool_val = (log_data < 0.0).mean()

    if average_bool_val > 0.8:

        if log_data.max() < 0.0:
            abs_log_data = abs(log_data)
        else:
            abs_log_data = abs(log_data - log_data.max())
    else:
        if log_data.min() > 0.0:
            abs_log_data = log_data
        else:
            abs_log_data = abs(log_data - log_data.min())

    log_abs_log_data = np.log(abs_log_data)

    result = self.make_linear_fit(axis=x_axis, data=log_abs_log_data)

    lifetime = np.exp(result.params['offset'].value)

    params['lifetime'].set(value=lifetime)

    return error, params

def make_baredoubleexponentialdecay_fit(self, x_axis, data, add_parameters=None):
    """
    This method performes a bare double exponential decay fit on the provided data.

    @param numpy.array x_axis: 1D axis values
    @param numpy.array data: 1D data, should have the same dimension as x_axis.
    @param dict add_parameters: Additional parameters

    @return object result: lmfit.model.ModelFit object, all parameters
                           provided about the fitting, like: success,
                           initial fitting values, best fitting values, data
                           with best fit with given axis,...
    """
    baredoubleexponentialdecay, params = self.make_baredoubleexponentialdecay_model()

    error, params = self.estimate_baredoubleexponentialdecay(x_axis, data, params)

    if add_parameters is not None:
        params = self._substitute_parameter(parameters=params,
                                            update_dict=add_parameters)
    try:
        result = baredoubleexponentialdecay.fit(data, x=x_axis, params=params)
    except:
        result = baredoubleexponentialdecay.fit(data, x=x_axis, params=params)
        logger.warning('The exponentialdecay with offset fit did not work. '
                       'Message: {}'.format(str(result.message)))
    return result

############################################################################
#                                                                          #
#                       double exponential decay                           #
#                                                                          #
############################################################################

def make_doubleexponentialdecay_model(self, prefix=None):
    """ Create a double exponential decay model.

    @param str prefix: optional string, which serves as a prefix for all
                       parameters used in this model. That will prevent
                       name collisions if this model is used in a composite
                       way.

    @return tuple: (object model, object params)

    Explanation of the objects:
        object lmfit.model.CompositeModel model:
            A model the lmfit module will use for that fit. Here a
            gaussian model. Returns an object of the class
            lmfit.model.CompositeModel.

        object lmfit.parameter.Parameters params:
            It is basically an OrderedDict, so a dictionary, with keys
            denoting the parameters as string names and values which are
            lmfit.parameter.Parameter (without s) objects, keeping the
            information about the current value.
    """

    bare_double_exp_decay, params = self.make_baredoubleexponentialdecay_model(prefix=prefix)
    ampitude_model, params = self.make_amplitude_model()

    double_exp_decay = ampitude_model*bare_double_exp_decay
    params = double_exp_decay.make_params()

    return double_exp_decay, params

def estimate_doubleexponentialdecay(self, x_axis, data, params):
    """ Provide an estimation for initial values for a double exponential decay.

    @param numpy.array x_axis: 1D axis values
    @param numpy.array data: 1D data, should have the same dimension as x_axis.
    @param lmfit.Parameters params: object includes parameter dictionary which
                                    can be set

    @return tuple (error, params):

    Explanation of the return parameter:
        int error: error code (0:OK, -1:error)
        Parameters object params: set parameters of initial values
    """

    error = self._check_1D_input(x_axis=x_axis, data=data, params=params)

    # remove all the data that can be smaller than or equals to data.std()
    # when the data is smaller than std of the data, it is beyond the resolution
    # which is not helpful to our fitting.
    for i in range(0, len(x_axis)):
        if data[i] <= data.std():
            break

    # take the logarithm of data, calculate the life time with linear fit.
    data_log = np.log(data[i])

    minimum = 2 * (x_axis[1]-x_axis[0])

    try:
        linear_result = self.make_linear_fit(axis=x_axis[0:i],
                                             data=data_log[0:i],
                                             add_parameters=None)

        params['lifetime'].set(value=-1/linear_result.params['slope'].value,
                               min=minimum)
        params['amplitude'].set(value=linear_result.params['offset'].value)

    except:
        params['lifetime'].set(value=x_axis[i]-x_axis[0], min=minimum)
        logger.error('Linear fit did not work in estimate_exponentialdecay.')

    return error, params

def make_doubleexponentialdecay_fit(self, x_axis, data, add_parameters=None):
    """
    This method performes a bare double exponential decay fit on the provided data.

    @param numpy.array x_axis: 1D axis values
    @param numpy.array data: 1D data, should have the same dimension as x_axis.
    @param dict add_parameters: Additional parameters

    @return object result: lmfit.model.ModelFit object, all parameters
                           provided about the fitting, like: success,
                           initial fitting values, best fitting values, data
                           with best fit with given axis,...
    """
    doubleexponentialdecay, params = self.make_doubleexponentialdecay_model()

    error, params = self.estimate_baredoubleexponentialdecay(x_axis, data, params)

    if add_parameters is not None:
        params = self._substitute_parameter(parameters=params,
                                            update_dict=add_parameters)
    try:
        result = doubleexponentialdecay.fit(data, x=x_axis, params=params)
    except:
        result = doubleexponentialdecay.fit(data, x=x_axis, params=params)
        logger.warning('The exponentialdecay with offset fit did not work. '
                       'Message: {}'.format(str(result.message)))
    return result


############################################################################
#                                                                          #
#                 double exponential decay with offset                     #
#                                                                          #
############################################################################

def make_doubleexponentialdecayoffset_model(self, prefix=None):
    """ Create a double exponential decay model with offset.

    @param str prefix: optional string, which serves as a prefix for all
                       parameters used in this model. That will prevent
                       name collisions if this model is used in a composite
                       way.

    @return tuple: (object model, object params)

    Explanation of the objects:
        object lmfit.model.CompositeModel model:
            A model the lmfit module will use for that fit. Here a
            gaussian model. Returns an object of the class
            lmfit.model.CompositeModel.

        object lmfit.parameter.Parameters params:
            It is basically an OrderedDict, so a dictionary, with keys
            denoting the parameters as string names and values which are
            lmfit.parameter.Parameter (without s) objects, keeping the
            information about the current value.
    """

    double_exp_decay, params = self.make_doubleexponentialdecay_model(prefix=prefix)
    offset_model, params = self.make_offset_model()

    double_exp_decay_offset = double_exp_decay + offset_model
    params = double_exp_decay_offset.make_params()

    return double_exp_decay_offset, params


############################################################################
#                                                                          #
#                 double exponential decay with offset                     #
#                                                                          #
############################################################################

def make_doubleexponentialdecayoffset_model(self, prefix=None):
    """ Create a double exponential decay model with offset.

    @param str prefix: optional string, which serves as a prefix for all
                       parameters used in this model. That will prevent
                       name collisions if this model is used in a composite
                       way.

    @return tuple: (object model, object params)

    Explanation of the objects:
        object lmfit.model.CompositeModel model:
            A model the lmfit module will use for that fit. Here a
            gaussian model. Returns an object of the class
            lmfit.model.CompositeModel.

        object lmfit.parameter.Parameters params:
            It is basically an OrderedDict, so a dictionary, with keys
            denoting the parameters as string names and values which are
            lmfit.parameter.Parameter (without s) objects, keeping the
            information about the current value.
    """

    bare_double_exp_decay, params = self.make_baredoubleexponentialdecay_model(prefix=prefix)
    ampitude_model, params = self.make_amplitude_model()
    constant_model, params = self.make_constant_model(prefix=prefix)

    double_exp_decay_offset = ampitude_model*bare_double_exp_decay + constant_model
    params = double_exp_decay_offset.make_params()

    return double_exp_decay_offset, params


############################################################################
#                                                                          #
#                  stretched exponential decay                             #
#                                                                          #
############################################################################

def make_stretchedexponentialdecay_model(self, prefix=None):
    """ Create a stretched exponential decay model.

    @param str prefix: optional string, which serves as a prefix for all
                       parameters used in this model. That will prevent
                       name collisions if this model is used in a composite
                       way.

    @return tuple: (object model, object params)

    Explanation of the objects:
        object lmfit.model.CompositeModel model:
            A model the lmfit module will use for that fit. Here a
            gaussian model. Returns an object of the class
            lmfit.model.CompositeModel.

        object lmfit.parameter.Parameters params:
            It is basically an OrderedDict, so a dictionary, with keys
            denoting the parameters as string names and values which are
            lmfit.parameter.Parameter (without s) objects, keeping the
            information about the current value.

    """

    bare_stre_exp_decay, params = self.make_barestretchedexponentialdecay_model(prefix=prefix)
    ampitude_model, params = self.make_amplitude_model()

    double_exp_decay_offset = ampitude_model*bare_stre_exp_decay
    params = double_exp_decay_offset.make_params()

    return double_exp_decay_offset, params



def estimate_stretchedexponentialdecay(self, x_axis, data, params):
    """ Provide an estimation for initial values for a stretched exponential decay.

    @param numpy.array x_axis: 1D axis values
    @param numpy.array data: 1D data, should have the same dimension as x_axis.
    @param lmfit.Parameters params: object includes parameter dictionary which
                                    can be set

    @return tuple (error, params):

    Explanation of the return parameter:
        int error: error code (0:OK, -1:error)
        Parameters object params: set parameters of initial values
    """

    error = self._check_1D_input(x_axis=x_axis, data=data, params=params)

    # remove all the data that can be smaller than or equals to data.std()
    # when the data is smaller than std of the data, it is beyond the resolution
    # which is not helpful to our fitting.
    for i in range(0, len(x_axis)):
        if data[i] <= data.std():
            break

    # take the logarithm of data, calculate the life time with linear fit.
    data_log = np.log(data[i])

    minimum = 2 * (x_axis[1]-x_axis[0])

    try:
        linear_result = self.make_linear_fit(axis=x_axis[0:i],
                                             data=data_log[0:i],
                                             add_parameters=None)

        params['lifetime'].set(value=-1/linear_result.params['slope'].value,
                               min=minimum)
        params['amplitude'].set(value=linear_result.params['offset'].value)

    except:
        params['lifetime'].set(value=x_axis[i]-x_axis[0], min=minimum)
        logger.error('Linear fit did not work in estimate_exponentialdecay.')

    return error, params





############################################################################
#                                                                          #
#             stretched exponential decay with offset                      #
#                                                                          #
############################################################################

def make_stretchedexponentialdecayoffset_model(self, prefix=None):
    """ Create a stretched exponential decay model with offset.

    @param str prefix: optional string, which serves as a prefix for all
                       parameters used in this model. That will prevent
                       name collisions if this model is used in a composite
                       way.

    @return tuple: (object model, object params)

    Explanation of the objects:
        object lmfit.model.CompositeModel model:
            A model the lmfit module will use for that fit. Here a
            gaussian model. Returns an object of the class
            lmfit.model.CompositeModel.

        object lmfit.parameter.Parameters params:
            It is basically an OrderedDict, so a dictionary, with keys
            denoting the parameters as string names and values which are
            lmfit.parameter.Parameter (without s) objects, keeping the
            information about the current value.

    """

    stre_exp_decay, params = self.make_stretchedexponentialdecay_model(prefix=prefix)
    constant_model, params = self.make_constant_model(prefix=prefix)

    stre_exp_decay_offset = stre_exp_decay + constant_model
    params = stre_exp_decay_offset.make_params()

    return stre_exp_decay_offset, params
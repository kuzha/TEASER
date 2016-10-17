#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example script for VDI 6007 simulation usage
"""

import numpy as np

import teaser.logic.simulation.VDI_6007.low_order_VDI as low_order_VDI
import teaser.logic.simulation.VDI_6007.weather as weat
from teaser.project import Project


def gen_res_type_example_building():
    """
    Generate example residential type building for VDI 6007 calculation

    Returns
    -------
    prj : object
        TEASER project instance
    """

    prj = Project(load_data=True)
    prj.name = "ArchetypeBuildings"
    prj.type_bldg_residential(name="ResidentialBuilding",
                              year_of_construction=1988,
                              number_of_floors=2,
                              height_of_floors=3.5,
                              net_leased_area=100,
                              with_ahu=True,
                              residential_layout=1,
                              neighbour_buildings=1,
                              attic=1,
                              cellar=1,
                              construction_type="heavy",
                              dormer=1)

    return prj


def vdi_example_6007(thermal_zone, weather):
    """
    Example function to perform VDI 6007 calculation with thermal_zone

    Parameters
    ----------
    thermal_zone : object
        TEASER thermal zone object
    weather : object
        Weather object of TEASER
    """

    #  Solar radiation
    #  Solar radiation input on each external area in W/m2
    #  solarRad_in = np.zeros((timesteps, 5))
    solarRad_in = np.transpose(
        weather.sun_rad)  # TODO: Check, if this is correct

    #  TODO: What is source_igRad
    source_igRad = np.zeros(timesteps)

    #  TODO: What is krad?
    krad = 1

    #  TODO: Calculate with function call
    #  Equal air temperature based on VDI in K
    #  equalAirTemp = np.zeros(timesteps) + 273.15 + 10
    equalAirTemp = weather.temp  # TODO: Substitute with equAir call

    #  Environment temperatures in K
    #  weatherTemperature = np.zeros(timesteps) + 273.15 + 10  # in K
    weatherTemperature = weather.temp

    #  Ventilation rate: Fresh air at temperature weatherTemperature in m3/s
    #  TODO: Substitute with TEASER call
    ventRate = np.zeros(timesteps)

    #  Internal convective gains in W
    #  TODO: Substitute with TEASER boundary conditions
    Q_ig = np.zeros(timesteps)

    #  TODO: Substitute with TEASER type building call
    # Load constant house parameters
    if len(thermal_zone.inner_walls) != 0:
        withInnerwalls = True
    else:
        withInnerwalls = False

    # Radiative heat transfer coef. between inner and outer walls in W/m2K
    #  TODO: Substitute with TEASER call
    alphaRad = np.zeros(timesteps) + 5

    #  Convert into house data dictionary
    houseData = {"R1i": thermal_zone.r1_iw,
                 "C1i": thermal_zone.c1_iw,
                 "Ai": thermal_zone.area_iw,
                 "RRest": thermal_zone.r_rest_ow,
                 "R1o": thermal_zone.r1_ow,
                 "C1o": thermal_zone.c1_ow,
                 "Ao": [thermal_zone.area_ow],
                 "Aw": thermal_zone.window_area_list,
                 "At": thermal_zone.window_area_list,
                 # Fixme: Is this correct?
                 "Vair": thermal_zone.volume,
                 "rhoair": thermal_zone.density_air,
                 "cair": thermal_zone.heat_capac_air,
                 "splitfac": thermal_zone.windows[0].a_conv,
                 # TODO: Is this correct?
                 "g": thermal_zone.weighted_g_value,
                 "alphaiwi": thermal_zone.alpha_comb_iw,
                 # TODO: Check, if this is correct
                 "alphaowi": thermal_zone.alpha_comb_inner_ow,
                 # TODO: Check, if this is correct
                 "alphaWall": thermal_zone.alpha_conv_outer_ow,
                 # TODO: Check, if this is correct
                 "withInnerwalls": withInnerwalls}  # TODO is this correct?

    # Define set points (prevent heating or cooling!)
    #  TODO: Calculate with function call
    t_set_heating = np.zeros(timesteps) + 273.15 + 20  # in Kelvin
    t_set_cooling = np.zeros(timesteps) + 273.15 + 24  # in Kelvin

    heater_limit = np.zeros((timesteps, 3)) + 1e10
    cooler_limit = np.zeros((timesteps, 3)) - 1e10

    # Calculate indoor air temperature
    T_air, Q_hc, Q_iw, Q_ow = \
        low_order_VDI.reducedOrderModelVDI(houseData=houseData,
                                           weatherTemperature=weatherTemperature,
                                           solarRad_in=solarRad_in,
                                           equalAirTemp=equalAirTemp,
                                           alphaRad=alphaRad,
                                           ventRate=ventRate,
                                           Q_ig=Q_ig,
                                           source_igRad=source_igRad,
                                           krad=krad,
                                           t_set_heating=t_set_heating,
                                           t_set_cooling=t_set_cooling,
                                           heater_limit=heater_limit,
                                           cooler_limit=cooler_limit)

    return (T_air, Q_hc, Q_iw, Q_ow)


if __name__ == '__main__':
    timesteps = 365 * 24

    beta = [45, 90, 90, 45, 90, 90]  # TODO: As default values for weather
    gamma = -np.array([0, 0, 90, 0, 180, 270])
    weather = weat.Weather(beta, gamma)

    #  Convert temperature to Kelvin
    weather.temp += 273.15

    #  Get TEASER project with residential type building
    prj = gen_res_type_example_building()

    #  Extract thermal_zone
    thermal_zone = prj.buildings[0].thermal_zones[0]

    #  Rund VDI 6007 example with thermal zone
    (T_air, Q_hc, Q_iw, Q_ow) = vdi_example_6007(thermal_zone, weather=weather)

    print('Indoor air temperature in Kelvin:')
    print(T_air)
    print()

    print('Heating(+) / cooling(-) load in Watt:')
    print(Q_hc)
    print()

    import matplotlib.pyplot as plt

    fig = plt.figure()
    fig.add_subplot(411)
    plt.plot(weather.temp - 273.15)
    plt.ylabel('Outdoor air\ntemperature in\ndegree Celsius')
    fig.add_subplot(412)
    plt.plot(weather.sun_rad[0])
    plt.ylabel('Sun radiation\non surface 0')  # TODO: Add unit
    fig.add_subplot(413)
    plt.plot(T_air - 273.15)
    plt.ylabel('Indoor air\ntemperature in\ndegree Celsius')
    fig.add_subplot(414)
    plt.plot(Q_hc / 1000)
    plt.ylabel('Heating/cooling\npower (+/-)\nin kW')
    plt.xlabel('Time in hours')
    plt.show()
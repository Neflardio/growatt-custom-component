"""Read status of growatt inverters."""
import datetime
import json
import logging
import re

#import growattServer
import voluptuous as vol

#Growatt Server paste start

from enum import IntEnum
import hashlib
import requests
import warnings

def hash_password(password):
    """
    Normal MD5, except add c if a byte of the digest is less than 10.
    """
    password_md5 = hashlib.md5(password.encode('utf-8')).hexdigest()
    for i in range(0, len(password_md5), 2):
        if password_md5[i] == '0':
            password_md5 = password_md5[0:i] + 'c' + password_md5[i + 1:]
    return password_md5

class Timespan(IntEnum):
    day = 1
    month = 2


class GrowattApi:
    server_url = 'http://server.growatt.com/'

    def __init__(self):
        self.session = requests.Session()

    def get_url(self, page):
        """
        Simple helper function to get the page url/
        """
        return self.server_url + page

    def login(self, username, password):
        """
        Log the user in.
        """
        password_md5 = hash_password(password)
        response = self.session.post(self.get_url('LoginAPI.do'), data={
            'userName': username,
            'password': password_md5
        })
        data = json.loads(response.content.decode('utf-8'))
        return data['back']

    def plant_list(self, user_id):
        """
        Get a list of plants connected to this account.
        """
        response = self.session.get(self.get_url('PlantListAPI.do'),
                                    params={'userId': user_id},
                                    allow_redirects=False)
        if response.status_code != 200:
            raise RuntimeError("Request failed: %s", response)
        data = json.loads(response.content.decode('utf-8'))
        return data['back']

    def plant_detail(self, plant_id, timespan, date):
        """
        Get plant details for specified timespan.
        """
        assert timespan in Timespan
        if timespan == Timespan.day:
            date_str = date.strftime('%Y-%m-%d')
        elif timespan == Timespan.month:
            date_str = date.strftime('%Y-%m')

        response = self.session.get(self.get_url('PlantDetailAPI.do'), params={
            'plantId': plant_id,
            'type': timespan.value,
            'date': date_str
        })
        data = json.loads(response.content.decode('utf-8'))
        return data['back']

    def inverter_data(self, inverter_id, date):
        """
        Get inverter data for specified date or today.
        """
        if date is None:
            date = datetime.date.today()
        date_str = date.strftime('%Y-%m-%d')
        response = self.session.get(self.get_url('newInverterAPI.do'), params={
            'op': 'getInverterData',
            'id': inverter_id,
            'type': 1,
            'date': date_str
        })
        data = json.loads(response.content.decode('utf-8'))
        return data

    def inverter_detail(self, inverter_id):
        """
        Get "All parameters" from PV inverter.
        """
        response = self.session.get(self.get_url('newInverterAPI.do'), params={
            'op': 'getInverterDetailData',
            'inverterId': inverter_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data

    def inverter_detail_two(self, inverter_id):
        """
        Get "All parameters" from PV inverter.
        """
        response = self.session.get(self.get_url('newInverterAPI.do'), params={
            'op': 'getInverterDetailData_two',
            'inverterId': inverter_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data

    def tlx_data(self, tlx_id, date):
        """
        Get inverter data for specified date or today.
        """
        if date is None:
            date = datetime.date.today()
        date_str = date.strftime('%Y-%m-%d')
        response = self.session.get(self.get_url('newTlxApi.do'), params={
            'op': 'getTlxData',
            'id': tlx_id,
            'type': 1,
            'date': date_str
        })
        data = json.loads(response.content.decode('utf-8'))
        return data

    def tlx_detail(self, tlx_id):
        """
        Get "All parameters" from PV inverter.
        """
        response = self.session.get(self.get_url('newTlxApi.do'), params={
            'op': 'getTlxDetailData',
            'id': tlx_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data

    def mix_info(self, mix_id):
        """
        Get "All parameters" from Mix device.
        """
        response = self.session.get(self.get_url('newMixApi.do'), params={
            'op': 'getMixInfo',
            'mixId': mix_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data

    def mix_info2(self, mix_id, plant_id):
        """
        Get "All parameters" from Mix device.
        """
        payloadbody = {'mixId':mix_id,'plantId': plant_id}
        response = self.session.post(self.get_url('newMixApi.do'), params={
            'op': 'getSystemStatus_KW'
        }, data=payloadbody)

        data = json.loads(response.content.decode('utf-8'))
        return data

    def storage_detail(self, storage_id):
        """
        Get "All parameters" from battery storage.
        """
        response = self.session.get(self.get_url('newStorageAPI.do'), params={
            'op': 'getStorageInfo_sacolar',
            'storageId': storage_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data

    def storage_params(self, storage_id):
        """
        Get much more detail from battery storage.
        """
        response = self.session.get(self.get_url('newStorageAPI.do'), params={
            'op': 'getStorageParams_sacolar',
            'storageId': storage_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data

    def storage_energy_overview(self, plant_id, storage_id):
        """
        Get some energy/generation overview data.
        """
        response = self.session.post(self.get_url('newStorageAPI.do?op=getEnergyOverviewData_sacolar'), params={
            'plantId': plant_id,
            'storageSn': storage_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data['obj']

    def inverter_list(self, plant_id):
        """
        Use device_list, it's more descriptive since the list contains more than inverters.
        """
        warnings.warn("This function may be deprecated in the future because naming is not correct, use device_list instead", DeprecationWarning)
        return self.device_list(plant_id)

    def device_list(self, plant_id):
        """
        Get a list of all devices connected to plant.
        """
        return self.plant_info(plant_id)['deviceList']

    def plant_info(self, plant_id):
        """
        Get basic plant information with device list.
        """
        response = self.session.get(self.get_url('newTwoPlantAPI.do'), params={
            'op': 'getAllDeviceList',
            'plantId': plant_id,
            'pageNum': 1,
            'pageSize': 1
        })

        data = json.loads(response.content.decode('utf-8'))
        return data

##Growatt Server paste end


from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_NAME,
    CONF_PASSWORD,
    CONF_USERNAME,
    ELECTRICAL_CURRENT_AMPERE,
    ENERGY_KILO_WATT_HOUR,
    FREQUENCY_HERTZ,
    POWER_WATT,
    POWER_KILO_WATT,
    TEMP_CELSIUS,
    VOLT,
    PERCENTAGE,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

CONF_PLANT_ID = "plant_id"
DEFAULT_PLANT_ID = "0"
DEFAULT_NAME = "Growatt"
SCAN_INTERVAL = datetime.timedelta(minutes=5)

# Sensor type order is: Sensor name, Unit of measurement, api data name, additional options

TOTAL_SENSOR_TYPES = {
    "total_money_today": ("Total money today", "€", "plantMoneyText", {}),
    "total_money_total": ("Money lifetime", "€", "totalMoneyText", {}),
    "total_energy_today": ("Energy Today", ENERGY_KILO_WATT_HOUR, "todayEnergy", {},),
    "total_output_power": (
        "Output Power",
        POWER_WATT,
        "invTodayPpv",
        {"device_class": "power"},
    ),
    "total_energy_output": (
        "Lifetime energy output",
        ENERGY_KILO_WATT_HOUR,
        "totalEnergy",
        {},
    ),
    "total_maximum_output": (
        "Maximum power",
        POWER_WATT,
        "nominalPower",
        {"device_class": "power"},
    ),
}

INVERTER_SENSOR_TYPES = {
    "inverter_energy_today": (
        "Energy today",
        ENERGY_KILO_WATT_HOUR,
        "powerToday",
        {"round": 1},
    ),
    "inverter_energy_total": (
        "Lifetime energy output",
        ENERGY_KILO_WATT_HOUR,
        "powerTotal",
        {"round": 1},
    ),
    "inverter_voltage_input_1": ("Input 1 voltage", VOLT, "vpv1", {"round": 2}),
    "inverter_amperage_input_1": (
        "Input 1 Amperage",
        ELECTRICAL_CURRENT_AMPERE,
        "ipv1",
        {"round": 1},
    ),
    "inverter_wattage_input_1": (
        "Input 1 Wattage",
        POWER_WATT,
        "ppv1",
        {"device_class": "power", "round": 1},
    ),
    "inverter_voltage_input_2": ("Input 2 voltage", VOLT, "vpv2", {"round": 1}),
    "inverter_amperage_input_2": (
        "Input 2 Amperage",
        ELECTRICAL_CURRENT_AMPERE,
        "ipv2",
        {"round": 1},
    ),
    "inverter_wattage_input_2": (
        "Input 2 Wattage",
        POWER_WATT,
        "ppv2",
        {"device_class": "power", "round": 1},
    ),
    "inverter_voltage_input_3": ("Input 3 voltage", VOLT, "vpv3", {"round": 1}),
    "inverter_amperage_input_3": (
        "Input 3 Amperage",
        ELECTRICAL_CURRENT_AMPERE,
        "ipv3",
        {"round": 1},
    ),
    "inverter_wattage_input_3": (
        "Input 3 Wattage",
        POWER_WATT,
        "ppv3",
        {"device_class": "power", "round": 1},
    ),
    "inverter_internal_wattage": (
        "Internal wattage",
        POWER_WATT,
        "ppv",
        {"device_class": "power", "round": 1},
    ),
    "inverter_reactive_voltage": ("Reactive voltage", VOLT, "vacr", {"round": 1}),
    "inverter_inverter_reactive_amperage": (
        "Reactive amperage",
        ELECTRICAL_CURRENT_AMPERE,
        "iacr",
        {"round": 1},
    ),
    "inverter_frequency": ("AC frequency", FREQUENCY_HERTZ, "fac", {"round": 1}),
    "inverter_current_wattage": (
        "Output power",
        POWER_WATT,
        "pac",
        {"device_class": "power", "round": 1},
    ),
    "inverter_current_reactive_wattage": (
        "Reactive wattage",
        POWER_WATT,
        "pacr",
        {"device_class": "power", "round": 1},
    ),
    "inverter_ipm_temperature": (
        "Intelligent Power Management temperature",
        TEMP_CELSIUS,
        "ipmTemperature",
        {"device_class": "temperature", "round": 1},
    ),
    "inverter_temperature": (
        "Temperature",
        TEMP_CELSIUS,
        "temperature",
        {"device_class": "temperature", "round": 1},
    ),
}

STORAGE_SENSOR_TYPES = {
    "storage_storage_production_today": (
        "Storage production today",
        ENERGY_KILO_WATT_HOUR,
        "eBatDisChargeToday",
        {},
    ),
    "storage_storage_production_lifetime": (
        "Lifetime Storage production",
        ENERGY_KILO_WATT_HOUR,
        "eBatDisChargeTotal",
        {},
    ),
    "storage_grid_discharge_today": (
        "Grid discharged today",
        ENERGY_KILO_WATT_HOUR,
        "eacDisChargeToday",
        {},
    ),
    "storage_load_consumption_today": (
        "Load consumption today",
        ENERGY_KILO_WATT_HOUR,
        "eopDischrToday",
        {},
    ),
    "storage_load_consumption_lifetime": (
        "Lifetime load consumption",
        ENERGY_KILO_WATT_HOUR,
        "eopDischrTotal",
        {},
    ),
    "storage_grid_charged_today": (
        "Grid charged today",
        ENERGY_KILO_WATT_HOUR,
        "eacChargeToday",
        {},
    ),
    "storage_charge_storage_lifetime": (
        "Lifetime storaged charged",
        ENERGY_KILO_WATT_HOUR,
        "eChargeTotal",
        {},
    ),
    "storage_solar_production": (
        "Solar power production",
        POWER_WATT,
        "ppv",
        {"device_class": "power"},
    ),
    "storage_battery_percentage": (
        "Battery percentage",
        "%",
        "capacity",
        {"device_class": "battery"},
    ),
    "storage_power_flow": (
        "Storage charging/ discharging(-ve)",
        POWER_WATT,
        "pCharge",
        {"device_class": "power"},
    ),
    "storage_load_consumption_solar_storage": (
        "Load consumption(Solar + Storage)",
        "VA",
        "rateVA",
        {},
    ),
    "storage_charge_today": (
        "Charge today",
        ENERGY_KILO_WATT_HOUR,
        "eChargeToday",
        {},
    ),
    "storage_import_from_grid": (
        "Import from grid",
        POWER_WATT,
        "pAcInPut",
        {"device_class": "power"},
    ),
    "storage_import_from_grid_today": (
        "Import from grid today",
        ENERGY_KILO_WATT_HOUR,
        "eToUserToday",
        {},
    ),
    "storage_import_from_grid_total": (
        "Import from grid total",
        ENERGY_KILO_WATT_HOUR,
        "eToUserTotal",
        {},
    ),
    "storage_load_consumption": (
        "Load consumption",
        POWER_WATT,
        "outPutPower",
        {"device_class": "power"},
    ),
    "storage_grid_voltage": ("AC input voltage", VOLT, "vGrid", {"round": 2}),
    "storage_pv_charging_voltage": ("PV charging voltage", VOLT, "vpv", {"round": 2}),
    "storage_ac_input_frequency_out": (
        "AC input frequency",
        FREQUENCY_HERTZ,
        "freqOutPut",
        {"round": 2},
    ),
    "storage_output_voltage": ("Output voltage", VOLT, "outPutVolt", {"round": 2}),
    "storage_ac_output_frequency": (
        "Ac output frequency",
        FREQUENCY_HERTZ,
        "freqGrid",
        {"round": 2},
    ),
    "storage_current_PV": (
        "Solar charge current",
        ELECTRICAL_CURRENT_AMPERE,
        "iAcCharge",
        {"round": 2},
    ),
    "storage_current_1": (
        "Solar current to storage",
        ELECTRICAL_CURRENT_AMPERE,
        "iChargePV1",
        {"round": 2},
    ),
    "storage_grid_amperage_input": (
        "Grid charge current",
        ELECTRICAL_CURRENT_AMPERE,
        "chgCurr",
        {"round": 2},
    ),
    "storage_grid_out_current": (
        "Grid out current",
        ELECTRICAL_CURRENT_AMPERE,
        "outPutCurrent",
        {"round": 2},
    ),
    "storage_battery_voltage": ("Battery voltage", VOLT, "vBat", {"round": 2}),
    "storage_load_percentage": (
        "Load percentage",
        "%",
        "loadPercent",
        {"device_class": "battery", "round": 2},
    ),
}

MIX_SENSOR_TYPES = {
    "inverter_voltage_input_1": (
        "Input 1 voltage", 
        VOLT,
        "vPv1",
        {"device_class": "power"}
    ),
    "inverter_voltage_input_2": (
        "Input 2 voltage", 
        VOLT,
        "vPv2",
        {"device_class": "power"}
    ),
    "battery_voltage": (
        "Battery voltage",
        VOLT,
        "vBat",
        {"device_class": "power"},
    ),
    "inverter_wattage_input_1": (
        "Input 1 Wattage",
        POWER_WATT,
        "pPv1",
        {"device_class": "power"},
    ),
    "inverter_wattage_input_2": (
        "Input 2 Wattage",
        POWER_WATT,
        "pPv2",
        {"device_class": "power"},
    ),
    "inverter_total_wattage": (
        "Total Input Wattage",
        POWER_KILO_WATT,
        "ppv",
        {"device_class": "power"},
    ),
    "current_load": (
        "Current Load",
        POWER_KILO_WATT,
        "pLocalLoad",
        {"device_class": "power"},
    ),
    "battery_discharge": (
        "Battery Discharge",
        POWER_KILO_WATT,
        "pdisCharge1",
        {"device_class": "power"},
    ),
    "export_to_grid": (
        "Export to Grid",
        POWER_KILO_WATT,
        "pactogrid",
        {"device_class": "power"},
    ),
    "battery_charge": (
        "Battery Charge",
        POWER_KILO_WATT,
        "chargePower",
        {"device_class": "power"},
    ),
    "battery_percent": (
        "Battery SOC",
        PERCENTAGE,
        "SOC",
        {"device_class": "power"},
    ),
}

TLX_SENSOR_TYPES = {
    "inverter_energy_today": (
        "Energy today",
        ENERGY_KILO_WATT_HOUR,
        "eacToday",
        {"round": 1},
    ),
    "inverter_energy_total": (
        "Lifetime energy output",
        ENERGY_KILO_WATT_HOUR,
        "eacTotal",
        {"round": 1},
    ),
    "inverter_voltage_input_1": ("Input 1 voltage", VOLT, "vpv1", {"round": 2}),
    "inverter_amperage_input_1": (
        "Input 1 Amperage",
        ELECTRICAL_CURRENT_AMPERE,
        "ipv1",
        {"round": 1},
    ),
    "inverter_wattage_input_1": (
        "Input 1 Wattage",
        POWER_WATT,
        "ppv1",
        {"device_class": "power", "round": 1},
    ),
    "inverter_voltage_input_2": ("Input 2 voltage", VOLT, "vpv2", {"round": 1}),
    "inverter_amperage_input_2": (
        "Input 2 Amperage",
        ELECTRICAL_CURRENT_AMPERE,
        "ipv2",
        {"round": 1},
    ),
    "inverter_wattage_input_2": (
        "Input 2 Wattage",
        POWER_WATT,
        "ppv2",
        {"device_class": "power", "round": 1},
    ),
    "inverter_voltage_input_3": ("Input 3 voltage", VOLT, "vpv3", {"round": 1}),
    "inverter_amperage_input_3": (
        "Input 3 Amperage",
        ELECTRICAL_CURRENT_AMPERE,
        "ipv3",
        {"round": 1},
    ),
    "inverter_wattage_input_3": (
        "Input 3 Wattage",
        POWER_WATT,
        "ppv3",
        {"device_class": "power", "round": 1},
    ),
    "inverter_internal_wattage": (
        "Internal wattage",
        POWER_WATT,
        "ppv",
        {"device_class": "power", "round": 1},
    ),
    "inverter_reactive_voltage": ("Reactive voltage", VOLT, "vacr", {"round": 1}),
    "inverter_inverter_reactive_amperage": (
        "Reactive amperage",
        ELECTRICAL_CURRENT_AMPERE,
        "iacr",
        {"round": 1},
    ),
    "inverter_frequency": ("AC frequency", FREQUENCY_HERTZ, "fac", {"round": 1}),
    "inverter_current_wattage": (
        "Output power",
        POWER_WATT,
        "pac",
        {"device_class": "power", "round": 1},
    ),
    "inverter_current_reactive_wattage": (
        "Reactive wattage",
        POWER_WATT,
        "pacr",
        {"device_class": "power", "round": 1},
    ),
    "temperature_1": (
        "Temperature 1",
        TEMP_CELSIUS,
        "temp1",
        {"device_class": "temperature", "round": 1},
    ),
    "temperature_2": (
        "Temperature 2",
        TEMP_CELSIUS,
        "temp2",
        {"device_class": "temperature", "round": 1},
    ),
    "temperature_3": (
        "Temperature 3",
        TEMP_CELSIUS,
        "temp3",
        {"device_class": "temperature", "round": 1},
    ),
    "temperature_4": (
        "Temperature 4",
        TEMP_CELSIUS,
        "temp4",
        {"device_class": "temperature", "round": 1},
    ),
    "temperature_5": (
        "Temperature 5",
        TEMP_CELSIUS,
        "temp5",
        {"device_class": "temperature", "round": 1},
    ),
}

SENSOR_TYPES = {**TOTAL_SENSOR_TYPES, **INVERTER_SENSOR_TYPES, **STORAGE_SENSOR_TYPES, **MIX_SENSOR_TYPES, **TLX_SENSOR_TYPES}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_PLANT_ID, default=DEFAULT_PLANT_ID): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Growatt sensor."""
    username = config[CONF_USERNAME]
    password = config[CONF_PASSWORD]
    plant_id = config[CONF_PLANT_ID]
    name = config[CONF_NAME]

    api = GrowattApi()

    # Log in to api and fetch first plant if no plant id is defined.
    login_response = api.login(username, password)
    if not login_response["success"] and login_response["errCode"] == "102":
        _LOGGER.error("Username or Password may be incorrect!")
        return
    user_id = login_response["userId"]
    if plant_id == DEFAULT_PLANT_ID:
        plant_info = api.plant_list(user_id)
        plant_id = plant_info["data"][0]["plantId"]

    # Get a list of devices for specified plant to add sensors for.
    devices = api.device_list(plant_id)
    entities = []
    probe = GrowattData(api, username, password, plant_id, "total")
    for sensor in TOTAL_SENSOR_TYPES:
        entities.append(
            GrowattInverter(probe, f"{name} Total", sensor, f"{plant_id}-{sensor}")
        )

    # Add sensors for each device in the specified plant.
    for device in devices:
        probe = GrowattData(
            api, username, password, device["deviceSn"], device["deviceType"]
        )
        sensors = []
        if device["deviceType"] == "inverter":
            sensors = INVERTER_SENSOR_TYPES
        elif device["deviceType"] == "mix":
            probe.plant_id = plant_id
            sensors = MIX_SENSOR_TYPES
        elif device["deviceType"] == "storage":
            probe.plant_id = plant_id
            sensors = STORAGE_SENSOR_TYPES
        else:
            _LOGGER.debug(
                "Device type %s was found but is not supported right now.",
                device["deviceType"],
            )

        for sensor in sensors:
            entities.append(
                GrowattInverter(
                    probe,
                    f"{device['deviceAilas']}",
                    sensor,
                    f"{device['deviceSn']}-{sensor}",
                )
            )

    add_entities(entities, True)


class GrowattInverter(Entity):
    """Representation of a Growatt Sensor."""

    def __init__(self, probe, name, sensor, unique_id):
        """Initialize a PVOutput sensor."""
        self.sensor = sensor
        self.probe = probe
        self._name = name
        self._state = None
        self._unique_id = unique_id

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._name} {SENSOR_TYPES[self.sensor][0]}"

    @property
    def unique_id(self):
        """Return the unique id of the sensor."""
        return self._unique_id

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:solar-power"

    @property
    def state(self):
        """Return the state of the sensor."""
        result = self.probe.get_data(SENSOR_TYPES[self.sensor][2])
        round_to = SENSOR_TYPES[self.sensor][3].get("round")
        if round_to is not None:
            result = round(result, round_to)
        return result

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return SENSOR_TYPES[self.sensor][3].get("device_class")

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return SENSOR_TYPES[self.sensor][1]

    def update(self):
        """Get the latest data from the Growat API and updates the state."""
        self.probe.update()


class GrowattData:
    """The class for handling data retrieval."""

    def __init__(self, api, username, password, device_id, growatt_type):
        """Initialize the probe."""

        self.growatt_type = growatt_type
        self.api = api
        self.device_id = device_id
        self.plant_id = None
        self.data = {}
        self.username = username
        self.password = password

    @Throttle(SCAN_INTERVAL)
    def update(self):
        """Update probe data."""
        self.api.login(self.username, self.password)
        _LOGGER.debug("Updating data for %s", self.device_id)
        try:
            if self.growatt_type == "total":
                total_info = self.api.plant_info(self.device_id)
                _LOGGER.debug("Updating Total data for %s", self.device_id)
                del total_info["deviceList"]
                # PlantMoneyText comes in as "3.1/€" remove anything that isn't part of the number
                total_info["plantMoneyText"] = re.sub(
                    r"[^\d.,]", "", total_info["plantMoneyText"]
                )
                self.data = total_info
                _LOGGER.debug(total_info)
            elif self.growatt_type == "inverter":
                _LOGGER.debug("Updating Inverter data for %s", self.device_id)
                inverter_info = self.api.inverter_detail(self.device_id)
                self.data = inverter_info
                _LOGGER.debug(inverter_info)
            elif self.growatt_type == "mix":
                _LOGGER.debug("Updating MIX data for %s", self.device_id)
                mix_info = self.api.mix_info2(self.device_id, self.plant_id)
                self.data = mix_info['obj']
                _LOGGER.debug(mix_info['obj'])
            elif self.growatt_type == "tlx":
                _LOGGER.debug("Updating TLX data for %s", self.device_id)
                tlx_info = self.api.tlx_detail(self.device_id)
                self.data = tlx_info['data']
                _LOGGER.debug(tlx_info['data'])
            elif self.growatt_type == "storage":
                _LOGGER.debug("Updating Storage data for %s", self.device_id)
                storage_info_detail = self.api.storage_params(self.device_id)[
                    "storageDetailBean"
                ]
                storage_energy_overview = self.api.storage_energy_overview(
                    self.plant_id, self.device_id
                )
                self.data = {**storage_info_detail, **storage_energy_overview}
                _LOGGER.debug(storage_info_detail)
                _LOGGER.debug(storage_energy_overview)
        except json.decoder.JSONDecodeError:
            _LOGGER.error("Unable to fetch data from Growatt server")

    def get_data(self, variable):
        """Get the data."""
        _LOGGER.debug("The value for %s is: %s", variable, self.data.get(variable))
        return self.data.get(variable)

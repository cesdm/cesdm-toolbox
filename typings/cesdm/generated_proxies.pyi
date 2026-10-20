from __future__ import annotations

from datetime import date, datetime
from typing import Any, Iterable
from cesdm.proxy import EntityProxy, FlatGroupViewProxy
from cesdm.default_library import *

class BoilerUnitCapacityExpansionProxy(FlatGroupViewProxy):
    commissioning_year: int | None
    retrofit_date: datetime | None
    retirement_date: datetime | None
    fixed_operating_cost: float | None

class BoilerUnitDispatchProxy(FlatGroupViewProxy):
    thermal_efficiency: float | None
    nominal_thermal_power_capacity: float | None
    minimum_load: float | None
    maximum_ramp_rate_up: float | None
    maximum_ramp_rate_down: float | None
    variable_operating_cost: float | None

class BoilerUnitTechnicalProxy(FlatGroupViewProxy):
    thermal_efficiency: float | None

class BoilerUnitTopologyProxy(FlatGroupViewProxy):
    @property
    def atFuelNode(self) -> NetworkNodeProxy | None: ...
    @atFuelNode.setter
    def atFuelNode(self, value: NetworkNodeProxy | str) -> None: ...
    @property
    def atHeatNode(self) -> HeatBusProxy | None: ...
    @atHeatNode.setter
    def atHeatNode(self, value: HeatBusProxy | str) -> None: ...

class CHPUnitCapacityExpansionProxy(FlatGroupViewProxy):
    commissioning_year: int | None
    retrofit_date: datetime | None
    retirement_date: datetime | None
    fixed_operating_cost: float | None

class CHPUnitDispatchProxy(FlatGroupViewProxy):
    nominal_electrical_power_capacity: float | None
    nominal_thermal_power_capacity: float | None
    electrical_efficiency: float | None
    thermal_efficiency: float | None
    minimum_load: float | None
    maximum_ramp_rate_up: float | None
    maximum_ramp_rate_down: float | None
    variable_operating_cost: float | None

class CHPUnitTechnicalProxy(FlatGroupViewProxy):
    electrical_efficiency: float | None
    thermal_efficiency: float | None
    total_efficiency: float | None
    power_to_heat_ratio: float | None

class CHPUnitTopologyProxy(FlatGroupViewProxy):
    @property
    def atFuelNode(self) -> NetworkNodeProxy | None: ...
    @atFuelNode.setter
    def atFuelNode(self, value: NetworkNodeProxy | str) -> None: ...
    @property
    def atElectricityNode(self) -> ElectricalBusProxy | None: ...
    @atElectricityNode.setter
    def atElectricityNode(self, value: ElectricalBusProxy | str) -> None: ...
    @property
    def atHeatNode(self) -> HeatBusProxy | None: ...
    @atHeatNode.setter
    def atHeatNode(self, value: HeatBusProxy | str) -> None: ...

class ConversionPortDispatchProxy(FlatGroupViewProxy):
    @property
    def hasFlowCoefficientProfile(self) -> ProfileProxy | None: ...
    @hasFlowCoefficientProfile.setter
    def hasFlowCoefficientProfile(self, value: ProfileProxy | str) -> None: ...

class DemandUnitCapacityExpansionProxy(FlatGroupViewProxy):
    commissioning_year: int | None
    retrofit_date: datetime | None
    retirement_date: datetime | None

class DemandUnitDispatchProxy(FlatGroupViewProxy):
    annual_energy_demand: float | None
    maximum_power_demand: float | None
    demand_type: str | None
    is_demand_flexible: bool | None
    flexibility_time_resolution: float | None
    flexibility_window_time_start: float | None
    flexibility_window_time_end: float | None
    maximum_upward_adjustment: float | None
    maximum_downward_adjustment: float | None
    value_of_lost_load: float | None
    variable_operating_cost: float | None
    @property
    def hasDemandProfile(self) -> ProfileProxy | None: ...
    @hasDemandProfile.setter
    def hasDemandProfile(self, value: ProfileProxy | str) -> None: ...

class DemandUnitTopologyProxy(FlatGroupViewProxy):
    @property
    def atNode(self) -> NetworkNodeProxy | None: ...
    @atNode.setter
    def atNode(self, value: NetworkNodeProxy | str) -> None: ...
    @property
    def belongsToGeographicalRegion(self) -> GeographicalRegionProxy | None: ...
    @belongsToGeographicalRegion.setter
    def belongsToGeographicalRegion(self, value: GeographicalRegionProxy | str) -> None: ...

class ElectricalBusSpatialProxy(FlatGroupViewProxy):
    latitude: float | None
    longitude: float | None
    elevation: float | None
    @property
    def belongsToGeographicalRegion(self) -> GeographicalRegionProxy | None: ...
    @belongsToGeographicalRegion.setter
    def belongsToGeographicalRegion(self, value: GeographicalRegionProxy | str) -> None: ...

class ElectrolyserUnitCapacityExpansionProxy(FlatGroupViewProxy):
    commissioning_year: int | None
    retrofit_date: datetime | None
    retirement_date: datetime | None
    fixed_operating_cost: float | None

class ElectrolyserUnitDispatchProxy(FlatGroupViewProxy):
    energy_conversion_efficiency: float | None
    nominal_electrical_power_capacity: float | None
    minimum_load: float | None
    maximum_ramp_rate_up: float | None
    maximum_ramp_rate_down: float | None
    variable_operating_cost: float | None

class ElectrolyserUnitTechnicalProxy(FlatGroupViewProxy):
    energy_conversion_efficiency: float | None

class ElectrolyserUnitTopologyProxy(FlatGroupViewProxy):
    @property
    def atElectricityNode(self) -> ElectricalBusProxy | None: ...
    @atElectricityNode.setter
    def atElectricityNode(self, value: ElectricalBusProxy | str) -> None: ...
    @property
    def atHydrogenNode(self) -> HydrogenBusProxy | None: ...
    @atHydrogenNode.setter
    def atHydrogenNode(self, value: HydrogenBusProxy | str) -> None: ...

class ExternalSupplyCapacityExpansionProxy(FlatGroupViewProxy):
    commissioning_year: int | None
    retrofit_date: datetime | None
    retirement_date: datetime | None

class ExternalSupplyDispatchProxy(FlatGroupViewProxy):
    supply_price: float | None
    supply_capacity: float | None
    is_slack: bool | None

class ExternalSupplyTopologyProxy(FlatGroupViewProxy):
    @property
    def atNode(self) -> NetworkNodeProxy | None: ...
    @atNode.setter
    def atNode(self, value: NetworkNodeProxy | str) -> None: ...
    @property
    def belongsToGeographicalRegion(self) -> GeographicalRegionProxy | None: ...
    @belongsToGeographicalRegion.setter
    def belongsToGeographicalRegion(self, value: GeographicalRegionProxy | str) -> None: ...

class FuelCellUnitCapacityExpansionProxy(FlatGroupViewProxy):
    commissioning_year: int | None
    retrofit_date: datetime | None
    retirement_date: datetime | None
    fixed_operating_cost: float | None

class FuelCellUnitDispatchProxy(FlatGroupViewProxy):
    electrical_efficiency: float | None
    thermal_efficiency: float | None
    nominal_electrical_power_capacity: float | None
    nominal_thermal_power_capacity: float | None
    minimum_load: float | None
    maximum_ramp_rate_up: float | None
    maximum_ramp_rate_down: float | None
    variable_operating_cost: float | None

class FuelCellUnitTechnicalProxy(FlatGroupViewProxy):
    electrical_efficiency: float | None
    thermal_efficiency: float | None
    power_to_heat_ratio: float | None

class FuelCellUnitTopologyProxy(FlatGroupViewProxy):
    @property
    def atHydrogenNode(self) -> HydrogenBusProxy | None: ...
    @atHydrogenNode.setter
    def atHydrogenNode(self, value: HydrogenBusProxy | str) -> None: ...
    @property
    def atFuelNode(self) -> NetworkNodeProxy | None: ...
    @atFuelNode.setter
    def atFuelNode(self, value: NetworkNodeProxy | str) -> None: ...
    @property
    def atElectricityNode(self) -> ElectricalBusProxy | None: ...
    @atElectricityNode.setter
    def atElectricityNode(self, value: ElectricalBusProxy | str) -> None: ...
    @property
    def atHeatNode(self) -> HeatBusProxy | None: ...
    @atHeatNode.setter
    def atHeatNode(self, value: HeatBusProxy | str) -> None: ...

class GasBusSpatialProxy(FlatGroupViewProxy):
    latitude: float | None
    longitude: float | None
    elevation: float | None
    @property
    def belongsToGeographicalRegion(self) -> GeographicalRegionProxy | None: ...
    @belongsToGeographicalRegion.setter
    def belongsToGeographicalRegion(self, value: GeographicalRegionProxy | str) -> None: ...

class GenerationUnitCapacityExpansionProxy(FlatGroupViewProxy):
    commissioning_year: int | None
    retrofit_date: datetime | None
    retirement_date: datetime | None

class GenerationUnitDispatchProxy(FlatGroupViewProxy):
    generator_technology_type: str | None
    nominal_power_capacity: float | None
    minimum_generation: float | None
    maximum_generation: float | None
    variable_operating_cost: float | None
    fixed_operating_cost: float | None
    energy_conversion_efficiency: float | None
    annual_resource_potential: float | None
    dispatch_type: str | None
    maximum_ramp_rate_up: float | None
    maximum_ramp_rate_down: float | None
    @property
    def hasAvailabilityProfile(self) -> ProfileProxy | None: ...
    @hasAvailabilityProfile.setter
    def hasAvailabilityProfile(self, value: ProfileProxy | str) -> None: ...

class GenerationUnitDynamicsProxy(FlatGroupViewProxy):
    rated_voltage: float | None
    rated_apparent_power: float | None

class GenerationUnitTechnicalProxy(FlatGroupViewProxy):
    rated_voltage: float | None
    rated_apparent_power: float | None

class GenerationUnitTopologyProxy(FlatGroupViewProxy):
    @property
    def atNode(self) -> NetworkNodeProxy | None: ...
    @atNode.setter
    def atNode(self, value: NetworkNodeProxy | str) -> None: ...
    @property
    def belongsToGeographicalRegion(self) -> GeographicalRegionProxy | None: ...
    @belongsToGeographicalRegion.setter
    def belongsToGeographicalRegion(self, value: GeographicalRegionProxy | str) -> None: ...

class GenericConversionUnitCapacityExpansionProxy(FlatGroupViewProxy):
    commissioning_year: int | None
    retrofit_date: datetime | None
    retirement_date: datetime | None

class GenericConversionUnitDispatchProxy(FlatGroupViewProxy):
    nominal_power_capacity: float | None
    @property
    def referencePort(self) -> ConversionPortProxy | None: ...
    @referencePort.setter
    def referencePort(self, value: ConversionPortProxy | str) -> None: ...

class GenericInterconnectorCapacityExpansionProxy(FlatGroupViewProxy):
    commissioning_year: int | None
    retrofit_date: datetime | None
    retirement_date: datetime | None

class GenericInterconnectorDispatchProxy(FlatGroupViewProxy):
    maximum_power_flow_from_to: float | None
    maximum_power_flow_to_from: float | None

class GenericInterconnectorPowerFlowProxy(FlatGroupViewProxy):
    maximum_power_flow_from_to: float | None
    maximum_power_flow_to_from: float | None

class GenericInterconnectorTopologyProxy(FlatGroupViewProxy):
    from_switch_closed: bool | None
    to_switch_closed: bool | None
    @property
    def fromNode(self) -> NetworkNodeProxy | None: ...
    @fromNode.setter
    def fromNode(self, value: NetworkNodeProxy | str) -> None: ...
    @property
    def toNode(self) -> NetworkNodeProxy | None: ...
    @toNode.setter
    def toNode(self, value: NetworkNodeProxy | str) -> None: ...
    @property
    def fromRegion(self) -> GeographicalRegionProxy | None: ...
    @fromRegion.setter
    def fromRegion(self, value: GeographicalRegionProxy | str) -> None: ...
    @property
    def toRegion(self) -> GeographicalRegionProxy | None: ...
    @toRegion.setter
    def toRegion(self, value: GeographicalRegionProxy | str) -> None: ...

class HVDCLinkCapacityExpansionProxy(FlatGroupViewProxy):
    commissioning_year: int | None
    retrofit_date: datetime | None
    retirement_date: datetime | None

class HVDCLinkDispatchProxy(FlatGroupViewProxy):
    max_flow: float | None
    variable_operating_cost: float | None

class HVDCLinkPowerFlowProxy(FlatGroupViewProxy):
    max_flow: float | None

class HVDCLinkTopologyProxy(FlatGroupViewProxy):
    from_switch_closed: bool | None
    to_switch_closed: bool | None
    @property
    def fromNode(self) -> ElectricalBusProxy | None: ...
    @fromNode.setter
    def fromNode(self, value: ElectricalBusProxy | str) -> None: ...
    @property
    def toNode(self) -> ElectricalBusProxy | None: ...
    @toNode.setter
    def toNode(self, value: ElectricalBusProxy | str) -> None: ...

class HeatBusSpatialProxy(FlatGroupViewProxy):
    latitude: float | None
    longitude: float | None
    elevation: float | None
    @property
    def belongsToGeographicalRegion(self) -> GeographicalRegionProxy | None: ...
    @belongsToGeographicalRegion.setter
    def belongsToGeographicalRegion(self, value: GeographicalRegionProxy | str) -> None: ...

class HeatPumpUnitCapacityExpansionProxy(FlatGroupViewProxy):
    commissioning_year: int | None
    retrofit_date: datetime | None
    retirement_date: datetime | None
    fixed_operating_cost: float | None

class HeatPumpUnitDispatchProxy(FlatGroupViewProxy):
    coefficient_of_performance: float | None
    nominal_thermal_power_capacity: float | None
    nominal_electrical_power_capacity: float | None
    minimum_load: float | None
    maximum_ramp_rate_up: float | None
    maximum_ramp_rate_down: float | None
    variable_operating_cost: float | None

class HeatPumpUnitTechnicalProxy(FlatGroupViewProxy):
    coefficient_of_performance: float | None

class HeatPumpUnitTopologyProxy(FlatGroupViewProxy):
    @property
    def atElectricityNode(self) -> ElectricalBusProxy | None: ...
    @atElectricityNode.setter
    def atElectricityNode(self, value: ElectricalBusProxy | str) -> None: ...
    @property
    def atHeatNode(self) -> HeatBusProxy | None: ...
    @atHeatNode.setter
    def atHeatNode(self, value: HeatBusProxy | str) -> None: ...

class HydroGenerationUnitCapacityExpansionProxy(FlatGroupViewProxy):
    commissioning_year: int | None
    retrofit_date: datetime | None
    retirement_date: datetime | None

class HydroGenerationUnitDispatchProxy(FlatGroupViewProxy):
    generator_technology_type: str | None
    nominal_power_capacity: float | None
    minimum_generation: float | None
    maximum_generation: float | None
    variable_operating_cost: float | None
    fixed_operating_cost: float | None
    energy_conversion_efficiency: float | None
    annual_resource_potential: float | None
    dispatch_type: str | None
    maximum_ramp_rate_up: float | None
    maximum_ramp_rate_down: float | None
    hydro_machine_kind: str | None
    turbine_efficiency: float | None
    maximum_pumping_power: float | None
    pumping_efficiency: float | None
    @property
    def hasAvailabilityProfile(self) -> ProfileProxy | None: ...
    @hasAvailabilityProfile.setter
    def hasAvailabilityProfile(self, value: ProfileProxy | str) -> None: ...

class HydroGenerationUnitDynamicsProxy(FlatGroupViewProxy):
    rated_voltage: float | None
    rated_apparent_power: float | None

class HydroGenerationUnitTechnicalProxy(FlatGroupViewProxy):
    rated_voltage: float | None
    rated_apparent_power: float | None

class HydroGenerationUnitTopologyProxy(FlatGroupViewProxy):
    @property
    def atNode(self) -> NetworkNodeProxy | None: ...
    @atNode.setter
    def atNode(self, value: NetworkNodeProxy | str) -> None: ...
    @property
    def belongsToGeographicalRegion(self) -> GeographicalRegionProxy | None: ...
    @belongsToGeographicalRegion.setter
    def belongsToGeographicalRegion(self, value: GeographicalRegionProxy | str) -> None: ...

class HydroReservoirCapacityExpansionProxy(FlatGroupViewProxy):
    commissioning_year: int | None
    retrofit_date: datetime | None
    retirement_date: datetime | None

class HydroReservoirDispatchProxy(FlatGroupViewProxy):
    energy_storage_capacity: float | None
    annual_natural_inflow_energy: float | None
    @property
    def hasNaturalInflowProfile(self) -> ProfileProxy | None: ...
    @hasNaturalInflowProfile.setter
    def hasNaturalInflowProfile(self, value: ProfileProxy | str) -> None: ...

class HydrogenBusSpatialProxy(FlatGroupViewProxy):
    latitude: float | None
    longitude: float | None
    elevation: float | None
    @property
    def belongsToGeographicalRegion(self) -> GeographicalRegionProxy | None: ...
    @belongsToGeographicalRegion.setter
    def belongsToGeographicalRegion(self, value: GeographicalRegionProxy | str) -> None: ...

class SolarGenerationUnitCapacityExpansionProxy(FlatGroupViewProxy):
    commissioning_year: int | None
    retrofit_date: datetime | None
    retirement_date: datetime | None

class SolarGenerationUnitDispatchProxy(FlatGroupViewProxy):
    generator_technology_type: str | None
    nominal_power_capacity: float | None
    minimum_generation: float | None
    maximum_generation: float | None
    variable_operating_cost: float | None
    fixed_operating_cost: float | None
    energy_conversion_efficiency: float | None
    annual_resource_potential: float | None
    dispatch_type: str | None
    maximum_ramp_rate_up: float | None
    maximum_ramp_rate_down: float | None
    @property
    def hasAvailabilityProfile(self) -> ProfileProxy | None: ...
    @hasAvailabilityProfile.setter
    def hasAvailabilityProfile(self, value: ProfileProxy | str) -> None: ...

class SolarGenerationUnitDynamicsProxy(FlatGroupViewProxy):
    rated_voltage: float | None
    rated_apparent_power: float | None

class SolarGenerationUnitTechnicalProxy(FlatGroupViewProxy):
    rated_voltage: float | None
    rated_apparent_power: float | None
    tilt_angle: float | None
    azimuth_angle: float | None
    tracking_type: str | None
    panel_technology: str | None

class SolarGenerationUnitTopologyProxy(FlatGroupViewProxy):
    @property
    def atNode(self) -> NetworkNodeProxy | None: ...
    @atNode.setter
    def atNode(self, value: NetworkNodeProxy | str) -> None: ...
    @property
    def belongsToGeographicalRegion(self) -> GeographicalRegionProxy | None: ...
    @belongsToGeographicalRegion.setter
    def belongsToGeographicalRegion(self, value: GeographicalRegionProxy | str) -> None: ...

class StorageUnitCapacityExpansionProxy(FlatGroupViewProxy):
    commissioning_year: int | None
    retrofit_date: datetime | None
    retirement_date: datetime | None

class StorageUnitDispatchProxy(FlatGroupViewProxy):
    nominal_power_capacity: float | None
    energy_storage_capacity: float | None
    annual_natural_inflow_energy: float | None
    charging_efficiency: float | None
    discharging_efficiency: float | None
    self_discharge_rate: float | None
    minimum_state_of_charge: float | None
    maximum_state_of_charge: float | None
    initial_state_of_charge: float | None
    maximum_ramp_rate_up: float | None
    maximum_ramp_rate_down: float | None
    variable_operating_cost: float | None
    charging_variable_operating_cost: float | None
    maximum_charging_power: float | None
    maximum_discharging_power: float | None
    storage_technology_type: str | None
    @property
    def hasNaturalInflowProfile(self) -> ProfileProxy | None: ...
    @hasNaturalInflowProfile.setter
    def hasNaturalInflowProfile(self, value: ProfileProxy | str) -> None: ...

class StorageUnitTopologyProxy(FlatGroupViewProxy):
    @property
    def atNode(self) -> NetworkNodeProxy | None: ...
    @atNode.setter
    def atNode(self, value: NetworkNodeProxy | str) -> None: ...
    @property
    def belongsToGeographicalRegion(self) -> GeographicalRegionProxy | None: ...
    @belongsToGeographicalRegion.setter
    def belongsToGeographicalRegion(self, value: GeographicalRegionProxy | str) -> None: ...

class ThermalGenerationUnitCapacityExpansionProxy(FlatGroupViewProxy):
    commissioning_year: int | None
    retrofit_date: datetime | None
    retirement_date: datetime | None

class ThermalGenerationUnitDispatchProxy(FlatGroupViewProxy):
    generator_technology_type: str | None
    nominal_power_capacity: float | None
    minimum_generation: float | None
    maximum_generation: float | None
    variable_operating_cost: float | None
    fixed_operating_cost: float | None
    energy_conversion_efficiency: float | None
    annual_resource_potential: float | None
    dispatch_type: str | None
    maximum_ramp_rate_up: float | None
    maximum_ramp_rate_down: float | None
    minimum_up_time: float | None
    minimum_down_time: float | None
    hot_start_cost: float | None
    cold_start_cost: float | None
    @property
    def hasAvailabilityProfile(self) -> ProfileProxy | None: ...
    @hasAvailabilityProfile.setter
    def hasAvailabilityProfile(self, value: ProfileProxy | str) -> None: ...

class ThermalGenerationUnitDynamicsProxy(FlatGroupViewProxy):
    rated_voltage: float | None
    rated_apparent_power: float | None

class ThermalGenerationUnitTechnicalProxy(FlatGroupViewProxy):
    rated_voltage: float | None
    rated_apparent_power: float | None
    cooling_type: str | None
    reactor_type: str | None
    reactor_thermal_power: float | None

class ThermalGenerationUnitTopologyProxy(FlatGroupViewProxy):
    @property
    def atNode(self) -> NetworkNodeProxy | None: ...
    @atNode.setter
    def atNode(self, value: NetworkNodeProxy | str) -> None: ...
    @property
    def belongsToGeographicalRegion(self) -> GeographicalRegionProxy | None: ...
    @belongsToGeographicalRegion.setter
    def belongsToGeographicalRegion(self, value: GeographicalRegionProxy | str) -> None: ...

class TransformerCapacityExpansionProxy(FlatGroupViewProxy):
    commissioning_year: int | None
    retrofit_date: datetime | None
    retirement_date: datetime | None

class TransformerDispatchProxy(FlatGroupViewProxy):
    thermal_capacity_rating: float | None

class TransformerPowerFlowProxy(FlatGroupViewProxy):
    thermal_capacity_rating: float | None

class TransformerTopologyProxy(FlatGroupViewProxy):
    from_switch_closed: bool | None
    to_switch_closed: bool | None
    @property
    def fromNode(self) -> ElectricalBusProxy | None: ...
    @fromNode.setter
    def fromNode(self, value: ElectricalBusProxy | str) -> None: ...
    @property
    def toNode(self) -> ElectricalBusProxy | None: ...
    @toNode.setter
    def toNode(self, value: ElectricalBusProxy | str) -> None: ...

class TransmissionLineCapacityExpansionProxy(FlatGroupViewProxy):
    commissioning_year: int | None
    retrofit_date: datetime | None
    retirement_date: datetime | None

class TransmissionLineDispatchProxy(FlatGroupViewProxy):
    thermal_capacity_rating: float | None

class TransmissionLinePowerFlowProxy(FlatGroupViewProxy):
    thermal_capacity_rating: float | None

class TransmissionLineTopologyProxy(FlatGroupViewProxy):
    from_switch_closed: bool | None
    to_switch_closed: bool | None
    @property
    def fromNode(self) -> ElectricalBusProxy | None: ...
    @fromNode.setter
    def fromNode(self, value: ElectricalBusProxy | str) -> None: ...
    @property
    def toNode(self) -> ElectricalBusProxy | None: ...
    @toNode.setter
    def toNode(self, value: ElectricalBusProxy | str) -> None: ...

class WindGenerationUnitCapacityExpansionProxy(FlatGroupViewProxy):
    commissioning_year: int | None
    retrofit_date: datetime | None
    retirement_date: datetime | None

class WindGenerationUnitDispatchProxy(FlatGroupViewProxy):
    generator_technology_type: str | None
    nominal_power_capacity: float | None
    minimum_generation: float | None
    maximum_generation: float | None
    variable_operating_cost: float | None
    fixed_operating_cost: float | None
    energy_conversion_efficiency: float | None
    annual_resource_potential: float | None
    dispatch_type: str | None
    maximum_ramp_rate_up: float | None
    maximum_ramp_rate_down: float | None
    @property
    def hasAvailabilityProfile(self) -> ProfileProxy | None: ...
    @hasAvailabilityProfile.setter
    def hasAvailabilityProfile(self, value: ProfileProxy | str) -> None: ...

class WindGenerationUnitDynamicsProxy(FlatGroupViewProxy):
    rated_voltage: float | None
    rated_apparent_power: float | None

class WindGenerationUnitTechnicalProxy(FlatGroupViewProxy):
    rated_voltage: float | None
    rated_apparent_power: float | None
    hub_height: float | None
    rotor_diameter: float | None
    installation_type: str | None
    number_of_turbines: int | None

class WindGenerationUnitTopologyProxy(FlatGroupViewProxy):
    @property
    def atNode(self) -> NetworkNodeProxy | None: ...
    @atNode.setter
    def atNode(self, value: NetworkNodeProxy | str) -> None: ...
    @property
    def belongsToGeographicalRegion(self) -> GeographicalRegionProxy | None: ...
    @belongsToGeographicalRegion.setter
    def belongsToGeographicalRegion(self, value: GeographicalRegionProxy | str) -> None: ...

class BoilerUnitProxy(EntityProxy):
    capacity_expansion: BoilerUnitCapacityExpansionProxy
    dispatch: BoilerUnitDispatchProxy
    technical: BoilerUnitTechnicalProxy
    topology: BoilerUnitTopologyProxy
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    commissioning_year: int | None
    """Year in which the generation unit was first commissioned and became commercially operational. Instance-specific: determines actual age, real efficiency relative to nameplate, and remaining technical lifetime. Year alone is sufficient for planning and ageing models."""
    retrofit_date: datetime | None
    """Date of major upgrade or efficiency retrofit. Impacts operational efficiency, lifetime extension, and emission calculations. Unit: date."""
    retirement_date: datetime | None
    """Planned or actual date when the generator is permanently retired from service. Used for asset replacement planning and system expansion studies. Unit: date."""
    thermal_efficiency: float | None
    """Ratio of useful heat output to fuel (or other input) energy for a compact ConversionUnit such as CHPUnit, BoilerUnit, or FuelCellUnit. Unit: fraction."""
    nominal_thermal_power_capacity: float | None
    """Maximum useful heat the conversion unit or its technology template can deliver, in MW. Applies to CHPUnit, HeatPumpUnit, BoilerUnit, and FuelCellUnit. Unit: MW."""
    minimum_load: float | None
    """Minimum stable operating load as a fraction of nominal electrical power. Unit: fraction."""
    maximum_ramp_rate_up: float | None
    """The maximum increase in output power per unit time, typically expressed in kW/s or MW/min. Represents the upward operational flexibility of the asset (a generator ramping up, or a storage device discharging faster). Unit: %/h."""
    maximum_ramp_rate_down: float | None
    """The maximum percentage decrease in output power per unit time during ramp-down operations. Expressed as %/min or %/s, capturing the asset's downward operational flexibility (a generator ramping down, or a storage device changing its charging/discharging rate). Unit: %/h."""
    variable_operating_cost: float | None
    """Marginal operating cost per unit of output (or throughput) used in dispatch optimisation. Unit: MU/MWh."""
    fixed_operating_cost: float | None
    """Fixed operation and maintenance (O&M) cost associated with the technology, typically expressed per year and per unit of installed capacity or per unit of technology. Covers costs that do not depend on energy production. Unit: MU/year, MU/(kW/year), MU/(MW/year), MU/unit."""
    @property
    def hasInputCarrier(self) -> CarrierProxy | None: ...
    @hasInputCarrier.setter
    def hasInputCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def hasHeatOutputCarrier(self) -> CarrierProxy | None: ...
    @hasHeatOutputCarrier.setter
    def hasHeatOutputCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def atFuelNode(self) -> NetworkNodeProxy | None: ...
    @atFuelNode.setter
    def atFuelNode(self, value: NetworkNodeProxy | str) -> None: ...
    @property
    def atHeatNode(self) -> HeatBusProxy | None: ...
    @atHeatNode.setter
    def atHeatNode(self, value: HeatBusProxy | str) -> None: ...

class CHPUnitProxy(EntityProxy):
    capacity_expansion: CHPUnitCapacityExpansionProxy
    dispatch: CHPUnitDispatchProxy
    technical: CHPUnitTechnicalProxy
    topology: CHPUnitTopologyProxy
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    commissioning_year: int | None
    """Year in which the generation unit was first commissioned and became commercially operational. Instance-specific: determines actual age, real efficiency relative to nameplate, and remaining technical lifetime. Year alone is sufficient for planning and ageing models."""
    retrofit_date: datetime | None
    """Date of major upgrade or efficiency retrofit. Impacts operational efficiency, lifetime extension, and emission calculations. Unit: date."""
    retirement_date: datetime | None
    """Planned or actual date when the generator is permanently retired from service. Used for asset replacement planning and system expansion studies. Unit: date."""
    nominal_electrical_power_capacity: float | None
    """Maximum electrical power (output or input rating) of a compact ConversionUnit such as CHPUnit, FuelCellUnit, HeatPumpUnit, or ElectrolyserUnit. Unit: MW."""
    nominal_thermal_power_capacity: float | None
    """Maximum useful heat the conversion unit or its technology template can deliver, in MW. Applies to CHPUnit, HeatPumpUnit, BoilerUnit, and FuelCellUnit. Unit: MW."""
    electrical_efficiency: float | None
    """Ratio of electrical energy output to fuel (or other input) energy for a compact ConversionUnit such as CHPUnit or FuelCellUnit. Unit: fraction."""
    thermal_efficiency: float | None
    """Ratio of useful heat output to fuel (or other input) energy for a compact ConversionUnit such as CHPUnit, BoilerUnit, or FuelCellUnit. Unit: fraction."""
    total_efficiency: float | None
    """Combined useful electrical and thermal output divided by fuel energy input. Unit: fraction."""
    power_to_heat_ratio: float | None
    """Ratio of electrical output to useful heat output of a compact ConversionUnit such as CHPUnit or FuelCellUnit. Unit: fraction."""
    minimum_load: float | None
    """Minimum stable operating load as a fraction of nominal electrical power. Unit: fraction."""
    maximum_ramp_rate_up: float | None
    """The maximum increase in output power per unit time, typically expressed in kW/s or MW/min. Represents the upward operational flexibility of the asset (a generator ramping up, or a storage device discharging faster). Unit: %/h."""
    maximum_ramp_rate_down: float | None
    """The maximum percentage decrease in output power per unit time during ramp-down operations. Expressed as %/min or %/s, capturing the asset's downward operational flexibility (a generator ramping down, or a storage device changing its charging/discharging rate). Unit: %/h."""
    variable_operating_cost: float | None
    """Marginal operating cost per unit of output (or throughput) used in dispatch optimisation. Unit: MU/MWh."""
    fixed_operating_cost: float | None
    """Fixed operation and maintenance (O&M) cost associated with the technology, typically expressed per year and per unit of installed capacity or per unit of technology. Covers costs that do not depend on energy production. Unit: MU/year, MU/(kW/year), MU/(MW/year), MU/unit."""
    @property
    def hasInputCarrier(self) -> CarrierProxy | None: ...
    @hasInputCarrier.setter
    def hasInputCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def hasElectricityOutputCarrier(self) -> CarrierProxy | None: ...
    @hasElectricityOutputCarrier.setter
    def hasElectricityOutputCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def hasHeatOutputCarrier(self) -> CarrierProxy | None: ...
    @hasHeatOutputCarrier.setter
    def hasHeatOutputCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def atFuelNode(self) -> NetworkNodeProxy | None: ...
    @atFuelNode.setter
    def atFuelNode(self, value: NetworkNodeProxy | str) -> None: ...
    @property
    def atElectricityNode(self) -> ElectricalBusProxy | None: ...
    @atElectricityNode.setter
    def atElectricityNode(self, value: ElectricalBusProxy | str) -> None: ...
    @property
    def atHeatNode(self) -> HeatBusProxy | None: ...
    @atHeatNode.setter
    def atHeatNode(self, value: HeatBusProxy | str) -> None: ...

class CarrierProxy(EntityProxy):
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    co2_emission_intensity: float | None
    """Mass of CO₂ emitted per unit of energy delivered by the carrier, expressed in tCO₂/MWh. Used for carbon accounting, emission constraint modelling, and environmental impact assessment. Unit: tCO2/MWh."""
    energy_carrier_cost: float | None
    """The monetary cost of the energy carrier per unit of energy, expressed in MU/MWh. Includes production, delivery, and variable operational costs, used for economic dispatch and optimization. Unit: MU/MWh."""
    carrier_group: str | None
    """High-level classification group of the carrier. Used for cross-carrier aggregation, reporting, and domain assignment. Network node types exist for electricity/gas/heat/hydrogen (ElectricalBus, GasBus, HeatBus, HydrogenBus). Group value "water" remains for carrier/resource labelling; hydro water balance uses HydroReservoir, not a WaterBus node."""
    carrier_type: str | None
    """Carrier category label (electricity, gas, heat, …) for classification or import mapping."""
    is_primary_fuel: bool | None
    """Indicates whether this carrier is a primary fuel that enters the system from outside the modelled boundary (e.g., natural gas, coal, crude oil). Mutually exclusive with is_secondary_fuel."""
    is_secondary_fuel: bool | None
    """Indicates whether this carrier is a secondary or derived fuel produced within the modelled system (e.g., hydrogen from electrolysis, synthetic methane). Mutually exclusive with is_primary_fuel."""

class CarrierDomainProxy(EntityProxy):
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    @property
    def hasCarrier(self) -> CarrierProxy: ...
    @hasCarrier.setter
    def hasCarrier(self, value: CarrierProxy | str) -> None: ...

class ConversionPortProxy(EntityProxy):
    dispatch: ConversionPortDispatchProxy
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    port_direction: str
    """Flow direction at a ConversionPort. input — carrier is consumed/withdrawn at this port output — carrier is produced/injected at this port bidirectional — carrier can flow in either direction (e.g. reversible heat pump, V2G)"""
    flow_coefficient: float
    """Signed flow ratio of a ConversionPort relative to the unit's reference port (reference port = 1.0)."""
    minimum_flow_fraction: float | None
    """Minimum allowed flow at this port as a fraction of the product flow_coefficient × reference_port_flow. Used to express minimum part-load ratios or technical minimum generation constraints at the port level."""
    maximum_flow_fraction: float | None
    """Maximum allowed flow at this port as a fraction of the product flow_coefficient × reference_port_flow. Values greater than 1.0 express short-term overload capability beyond the rated coefficient."""
    nominal_power_capacity: float | None
    """Maximum instantaneous power the asset, technology template, or conversion port can deliver or absorb, in MW. Defines operational limits for dispatch. Unit: MW."""
    @property
    def belongsToUnit(self) -> ConversionUnitProxy: ...
    @belongsToUnit.setter
    def belongsToUnit(self, value: ConversionUnitProxy | str) -> None: ...
    @property
    def atNode(self) -> NetworkNodeProxy: ...
    @atNode.setter
    def atNode(self, value: NetworkNodeProxy | str) -> None: ...
    @property
    def hasCarrier(self) -> CarrierProxy: ...
    @hasCarrier.setter
    def hasCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def hasFlowCoefficientProfile(self) -> ProfileProxy | None: ...
    @hasFlowCoefficientProfile.setter
    def hasFlowCoefficientProfile(self, value: ProfileProxy | str) -> None: ...

class ConversionUnitProxy(EntityProxy):
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    commissioning_year: int | None
    """Year in which the generation unit was first commissioned and became commercially operational. Instance-specific: determines actual age, real efficiency relative to nameplate, and remaining technical lifetime. Year alone is sufficient for planning and ageing models."""
    retrofit_date: datetime | None
    """Date of major upgrade or efficiency retrofit. Impacts operational efficiency, lifetime extension, and emission calculations. Unit: date."""
    retirement_date: datetime | None
    """Planned or actual date when the generator is permanently retired from service. Used for asset replacement planning and system expansion studies. Unit: date."""

class DemandUnitProxy(EntityProxy):
    capacity_expansion: DemandUnitCapacityExpansionProxy
    dispatch: DemandUnitDispatchProxy
    topology: DemandUnitTopologyProxy
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    commissioning_year: int | None
    """Year in which the generation unit was first commissioned and became commercially operational. Instance-specific: determines actual age, real efficiency relative to nameplate, and remaining technical lifetime. Year alone is sufficient for planning and ageing models."""
    retrofit_date: datetime | None
    """Date of major upgrade or efficiency retrofit. Impacts operational efficiency, lifetime extension, and emission calculations. Unit: date."""
    retirement_date: datetime | None
    """Planned or actual date when the generator is permanently retired from service. Used for asset replacement planning and system expansion studies. Unit: date."""
    annual_energy_demand: float | None
    """The total amount of energy required by the load over an entire year, expressed in MWh/year. It is used to scale demand time series or to validate consumption totals for modelling scenarios. Unit: MWh/year."""
    maximum_power_demand: float | None
    """Peak power the load can withdraw, in MW. The yearly energy is annual_energy_demand. Unit: MW."""
    demand_type: str | None
    """Demand category or sector label for a DemandUnit (industrial, residential, …)."""
    is_demand_flexible: bool | None
    """Boolean indicator specifying whether the load can be shifted, curtailed, rescheduled, or otherwise managed during operation. If false, demand must be met as defined by the demand profile."""
    flexibility_time_resolution: float | None
    """The smallest allowable time granularity for shifting, adjusting, or rescheduling the load demand. Typically corresponds to the dispatch interval (e.g., 15 min, 1 h). Unit: h, min."""
    flexibility_window_time_start: float | None
    """The beginning of the time interval during which the load is allowed to shift or modify its consumption, expressed as a timestamp or model time index. Unit: Timestamp / time index."""
    flexibility_window_time_end: float | None
    """The end of the time interval during which flexibility actions are permitted. Outside this window the demand must strictly follow its profile. Unit: Timestamp / time index."""
    maximum_upward_adjustment: float | None
    """The maximum amount of incremental upward deviation from the nominal load that is allowed at any given time, expressed in kW or MW. Represents demand increase or load activation flexibility. Unit: kW, MW."""
    maximum_downward_adjustment: float | None
    """The maximum allowable reduction from the nominal load, expressed in kW or MW. Represents demand reduction, curtailment potential, or flexibility for load shedding. Unit: kW, MW."""
    value_of_lost_load: float | None
    """The economic cost (MU/MWh) assigned to unserved energy demand, representing the penalty for not meeting the load. This parameter quantifies the societal and economic impact of supply interruptions and is heavily used in adequacy and reliability studies. Unit: MU/MWh."""
    variable_operating_cost: float | None
    """Marginal operating cost per unit of output (or throughput) used in dispatch optimisation. Unit: MU/MWh."""
    @property
    def hasCarrier(self) -> CarrierProxy | None: ...
    @hasCarrier.setter
    def hasCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def hasDemandProfile(self) -> ProfileProxy | None: ...
    @hasDemandProfile.setter
    def hasDemandProfile(self, value: ProfileProxy | str) -> None: ...
    @property
    def atNode(self) -> NetworkNodeProxy | None: ...
    @atNode.setter
    def atNode(self, value: NetworkNodeProxy | str) -> None: ...
    @property
    def belongsToGeographicalRegion(self) -> GeographicalRegionProxy | None: ...
    @belongsToGeographicalRegion.setter
    def belongsToGeographicalRegion(self, value: GeographicalRegionProxy | str) -> None: ...

class ElectricalBusProxy(EntityProxy):
    spatial: ElectricalBusSpatialProxy
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    latitude: float | None
    """Geographical latitude of the entity, expressed in decimal degrees. Used for spatial modelling, renewable resource assessment, and GIS-based visualisation. Unit: deg."""
    longitude: float | None
    """Geographical longitude of the entity, expressed in decimal degrees. Used for spatial modelling, renewable resource assessment, and GIS-based visualisation. Unit: deg."""
    elevation: float | None
    """Elevation of the entity above mean sea level, expressed in metres. Relevant for climate-adjusted performance modelling and topographic network studies. Unit: m."""
    nominal_voltage: float | None
    """Rated line-to-line voltage of the network node or branch under normal operating conditions, expressed in kV. Unit: kV."""
    @property
    def belongsToGeographicalRegion(self) -> GeographicalRegionProxy | None: ...
    @belongsToGeographicalRegion.setter
    def belongsToGeographicalRegion(self, value: GeographicalRegionProxy | str) -> None: ...
    @property
    def belongsToCarrierDomain(self) -> CarrierDomainProxy: ...
    @belongsToCarrierDomain.setter
    def belongsToCarrierDomain(self, value: CarrierDomainProxy | str) -> None: ...

class ElectricityTransmissionProxy(EntityProxy):
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    commissioning_year: int | None
    """Year in which the generation unit was first commissioned and became commercially operational. Instance-specific: determines actual age, real efficiency relative to nameplate, and remaining technical lifetime. Year alone is sufficient for planning and ageing models."""
    retrofit_date: datetime | None
    """Date of major upgrade or efficiency retrofit. Impacts operational efficiency, lifetime extension, and emission calculations. Unit: date."""
    retirement_date: datetime | None
    """Planned or actual date when the generator is permanently retired from service. Used for asset replacement planning and system expansion studies. Unit: date."""
    from_switch_closed: bool | None
    """Boolean indicating whether the breaker at the from-end of the branch is closed (true = connected, false = disconnected). Used in contingency and outage modelling."""
    to_switch_closed: bool | None
    """Boolean indicating whether the breaker at the to-end of the branch is closed (true = connected, false = disconnected). Used in contingency and outage modelling."""
    @property
    def fromNode(self) -> ElectricalBusProxy | None: ...
    @fromNode.setter
    def fromNode(self, value: ElectricalBusProxy | str) -> None: ...
    @property
    def toNode(self) -> ElectricalBusProxy | None: ...
    @toNode.setter
    def toNode(self, value: ElectricalBusProxy | str) -> None: ...

class ElectrolyserUnitProxy(EntityProxy):
    capacity_expansion: ElectrolyserUnitCapacityExpansionProxy
    dispatch: ElectrolyserUnitDispatchProxy
    technical: ElectrolyserUnitTechnicalProxy
    topology: ElectrolyserUnitTopologyProxy
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    commissioning_year: int | None
    """Year in which the generation unit was first commissioned and became commercially operational. Instance-specific: determines actual age, real efficiency relative to nameplate, and remaining technical lifetime. Year alone is sufficient for planning and ageing models."""
    retrofit_date: datetime | None
    """Date of major upgrade or efficiency retrofit. Impacts operational efficiency, lifetime extension, and emission calculations. Unit: date."""
    retirement_date: datetime | None
    """Planned or actual date when the generator is permanently retired from service. Used for asset replacement planning and system expansion studies. Unit: date."""
    energy_conversion_efficiency: float | None
    """Ratio of useful output energy to input energy, expressed as a fraction (0–1). Determines efficiency of energy conversion processes. Unit: fraction."""
    nominal_electrical_power_capacity: float | None
    """Maximum electrical power (output or input rating) of a compact ConversionUnit such as CHPUnit, FuelCellUnit, HeatPumpUnit, or ElectrolyserUnit. Unit: MW."""
    minimum_load: float | None
    """Minimum stable operating load as a fraction of nominal electrical power. Unit: fraction."""
    maximum_ramp_rate_up: float | None
    """The maximum increase in output power per unit time, typically expressed in kW/s or MW/min. Represents the upward operational flexibility of the asset (a generator ramping up, or a storage device discharging faster). Unit: %/h."""
    maximum_ramp_rate_down: float | None
    """The maximum percentage decrease in output power per unit time during ramp-down operations. Expressed as %/min or %/s, capturing the asset's downward operational flexibility (a generator ramping down, or a storage device changing its charging/discharging rate). Unit: %/h."""
    variable_operating_cost: float | None
    """Marginal operating cost per unit of output (or throughput) used in dispatch optimisation. Unit: MU/MWh."""
    fixed_operating_cost: float | None
    """Fixed operation and maintenance (O&M) cost associated with the technology, typically expressed per year and per unit of installed capacity or per unit of technology. Covers costs that do not depend on energy production. Unit: MU/year, MU/(kW/year), MU/(MW/year), MU/unit."""
    @property
    def hasInputCarrier(self) -> CarrierProxy | None: ...
    @hasInputCarrier.setter
    def hasInputCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def hasHydrogenOutputCarrier(self) -> CarrierProxy | None: ...
    @hasHydrogenOutputCarrier.setter
    def hasHydrogenOutputCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def atElectricityNode(self) -> ElectricalBusProxy | None: ...
    @atElectricityNode.setter
    def atElectricityNode(self, value: ElectricalBusProxy | str) -> None: ...
    @property
    def atHydrogenNode(self) -> HydrogenBusProxy | None: ...
    @atHydrogenNode.setter
    def atHydrogenNode(self, value: HydrogenBusProxy | str) -> None: ...

class EnergyAssetInstanceProxy(EntityProxy):
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    commissioning_year: int | None
    """Year in which the generation unit was first commissioned and became commercially operational. Instance-specific: determines actual age, real efficiency relative to nameplate, and remaining technical lifetime. Year alone is sufficient for planning and ageing models."""
    retrofit_date: datetime | None
    """Date of major upgrade or efficiency retrofit. Impacts operational efficiency, lifetime extension, and emission calculations. Unit: date."""
    retirement_date: datetime | None
    """Planned or actual date when the generator is permanently retired from service. Used for asset replacement planning and system expansion studies. Unit: date."""

class EnergySystemModelProxy(EntityProxy):
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    base_mva: float | None
    """The system-wide apparent power base used for per-unit calculations. All per-unit quantities are referenced to this base power. Unit: MW."""
    co2_price: float | None
    """CO2 Price is a monetary value assigned to each tonne of carbon dioxide (or CO₂-equivalent) emitted within an energy system. It represents the cost of emitting greenhouse gases and is used to internalize the environmental and societal damages associated with climate change. Unit: MU/tCO2, CHF/tCO2."""

class EnergyTechnologyTypeProxy(EntityProxy):
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    energy_conversion_efficiency: float | None
    """Ratio of useful output energy to input energy, expressed as a fraction (0–1). Determines efficiency of energy conversion processes. Unit: fraction."""
    dispatch_type: str | None
    """Dispatch classification of a generation technology: "dispatchable" — operator can choose output (thermal, hydro reservoir) "nondispatchable" — output bounded by external resource (wind, solar, RoR) "must_run" — must generate at minimum level (nuclear baseload, CHP)"""
    variable_operating_cost: float | None
    """Marginal operating cost per unit of output (or throughput) used in dispatch optimisation. Unit: MU/MWh."""
    fixed_operating_cost: float | None
    """Fixed operation and maintenance (O&M) cost associated with the technology, typically expressed per year and per unit of installed capacity or per unit of technology. Covers costs that do not depend on energy production. Unit: MU/year, MU/(kW/year), MU/(MW/year), MU/unit."""
    investment_cost: float | None
    """Overnight investment cost of the technology per unit of installed capacity or per unit, depending on the modeling convention. Used together with technical_lifetime and discount_rate for annualized cost calculations. Unit: MU/kW, MU/MW, MU/unit."""
    technical_lifetime: float | None
    """Technical lifetime of the asset in years. Unit: years."""
    discount_rate: float | None
    """Discount rate applied to investment and cost streams associated with this technology, expressed as a fraction between 0 and 1 (e.g. 0.03 for 3%). May override a global discount rate defined at the Energy System Model level. Unit: fraction."""
    salvage_fraction_value: float | None
    """Fraction of the original investment value that is recovered as salvage at the end of the planning horizon, expressed as a fraction between 0 and 1. Used for partial lifetime treatment when the technology lifetime extends beyond the modeled period. Unit: fraction."""
    maximum_ramp_rate_up: float | None
    """The maximum increase in output power per unit time, typically expressed in kW/s or MW/min. Represents the upward operational flexibility of the asset (a generator ramping up, or a storage device discharging faster). Unit: %/h."""
    maximum_ramp_rate_down: float | None
    """The maximum percentage decrease in output power per unit time during ramp-down operations. Expressed as %/min or %/s, capturing the asset's downward operational flexibility (a generator ramping down, or a storage device changing its charging/discharging rate). Unit: %/h."""
    minimum_up_time: float | None
    """Minimum number of hours a unit must remain online once started. Used in unit commitment models. Unit: h."""
    minimum_down_time: float | None
    """Minimum number of hours a unit must remain offline after shutdown. Used in unit commitment models. Unit: h."""
    hot_start_cost: float | None
    """Cost incurred to restart a generator that has been recently offline (hot state), expressed in monitary units. Reflects fuel and operational overhead. Unit: MU."""
    cold_start_cost: float | None
    """Cost incurred to restart a generator that has been offline for a long period (cold state), expressed in MU. Usually higher than hot start due to additional operational procedures. Unit: MU."""
    ramping_cost_increase: float | None
    """The cost associated with increasing output power, expressed in MU/MW or MU/MW/min. Used in dispatch optimisation to represent wear, thermal cycling, or operational penalties for fast upward ramping. Unit: MU/MW."""
    ramping_cost_decrease: float | None
    """The cost associated with reducing output power or reducing charging rate, expressed in MonetaryUnits/MW or MonetaryUnits/MW/min. Represents operational constraints or efficiency penalties during ramp-down."""
    generator_technology_type: str | None
    """Generation technology category when no GeneratorType library entity is referenced."""
    comment: str | None
    """Optional comment/notes."""

class ExternalSupplyProxy(EntityProxy):
    capacity_expansion: ExternalSupplyCapacityExpansionProxy
    dispatch: ExternalSupplyDispatchProxy
    topology: ExternalSupplyTopologyProxy
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    commissioning_year: int | None
    """Year in which the generation unit was first commissioned and became commercially operational. Instance-specific: determines actual age, real efficiency relative to nameplate, and remaining technical lifetime. Year alone is sufficient for planning and ageing models."""
    retrofit_date: datetime | None
    """Date of major upgrade or efficiency retrofit. Impacts operational efficiency, lifetime extension, and emission calculations. Unit: date."""
    retirement_date: datetime | None
    """Planned or actual date when the generator is permanently retired from service. Used for asset replacement planning and system expansion studies. Unit: date."""
    supply_price: float | None
    """Marginal price at which the external supply injects energy into the system [MU/MWh]. Acts as the cost signal for the slack source in economic dispatch and market clearing. Set to 0 for a free slack (e.g. reference bus in a power flow). Set to a large positive value (e.g. value_of_lost_load) to represent an emergency import of last resort. Unit: MU/MWh."""
    supply_capacity: float | None
    """Maximum power the external supply can inject [MW]. When absent or null the supply is treated as uncapacitated (true slack — unlimited injection). Set an explicit value to model a capacity-limited import connection such as a cross-border cable. Unit: MW."""
    is_slack: bool | None
    """Boolean flag indicating that this ExternalSupply acts as the system slack / reference node. Exactly one ExternalSupply per connected island should have is_slack = true. When true, the supply absorbs all active power imbalances and the connected bus is treated as the angle reference in AC power flow (bus type = slack)."""
    @property
    def hasOutputCarrier(self) -> CarrierProxy | None: ...
    @hasOutputCarrier.setter
    def hasOutputCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def atNode(self) -> NetworkNodeProxy | None: ...
    @atNode.setter
    def atNode(self, value: NetworkNodeProxy | str) -> None: ...
    @property
    def belongsToGeographicalRegion(self) -> GeographicalRegionProxy | None: ...
    @belongsToGeographicalRegion.setter
    def belongsToGeographicalRegion(self, value: GeographicalRegionProxy | str) -> None: ...

class FuelCellUnitProxy(EntityProxy):
    capacity_expansion: FuelCellUnitCapacityExpansionProxy
    dispatch: FuelCellUnitDispatchProxy
    technical: FuelCellUnitTechnicalProxy
    topology: FuelCellUnitTopologyProxy
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    commissioning_year: int | None
    """Year in which the generation unit was first commissioned and became commercially operational. Instance-specific: determines actual age, real efficiency relative to nameplate, and remaining technical lifetime. Year alone is sufficient for planning and ageing models."""
    retrofit_date: datetime | None
    """Date of major upgrade or efficiency retrofit. Impacts operational efficiency, lifetime extension, and emission calculations. Unit: date."""
    retirement_date: datetime | None
    """Planned or actual date when the generator is permanently retired from service. Used for asset replacement planning and system expansion studies. Unit: date."""
    electrical_efficiency: float | None
    """Ratio of electrical energy output to fuel (or other input) energy for a compact ConversionUnit such as CHPUnit or FuelCellUnit. Unit: fraction."""
    thermal_efficiency: float | None
    """Ratio of useful heat output to fuel (or other input) energy for a compact ConversionUnit such as CHPUnit, BoilerUnit, or FuelCellUnit. Unit: fraction."""
    nominal_electrical_power_capacity: float | None
    """Maximum electrical power (output or input rating) of a compact ConversionUnit such as CHPUnit, FuelCellUnit, HeatPumpUnit, or ElectrolyserUnit. Unit: MW."""
    nominal_thermal_power_capacity: float | None
    """Maximum useful heat the conversion unit or its technology template can deliver, in MW. Applies to CHPUnit, HeatPumpUnit, BoilerUnit, and FuelCellUnit. Unit: MW."""
    power_to_heat_ratio: float | None
    """Ratio of electrical output to useful heat output of a compact ConversionUnit such as CHPUnit or FuelCellUnit. Unit: fraction."""
    minimum_load: float | None
    """Minimum stable operating load as a fraction of nominal electrical power. Unit: fraction."""
    maximum_ramp_rate_up: float | None
    """The maximum increase in output power per unit time, typically expressed in kW/s or MW/min. Represents the upward operational flexibility of the asset (a generator ramping up, or a storage device discharging faster). Unit: %/h."""
    maximum_ramp_rate_down: float | None
    """The maximum percentage decrease in output power per unit time during ramp-down operations. Expressed as %/min or %/s, capturing the asset's downward operational flexibility (a generator ramping down, or a storage device changing its charging/discharging rate). Unit: %/h."""
    variable_operating_cost: float | None
    """Marginal operating cost per unit of output (or throughput) used in dispatch optimisation. Unit: MU/MWh."""
    fixed_operating_cost: float | None
    """Fixed operation and maintenance (O&M) cost associated with the technology, typically expressed per year and per unit of installed capacity or per unit of technology. Covers costs that do not depend on energy production. Unit: MU/year, MU/(kW/year), MU/(MW/year), MU/unit."""
    @property
    def hasInputCarrier(self) -> CarrierProxy | None: ...
    @hasInputCarrier.setter
    def hasInputCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def hasElectricityOutputCarrier(self) -> CarrierProxy | None: ...
    @hasElectricityOutputCarrier.setter
    def hasElectricityOutputCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def hasHeatOutputCarrier(self) -> CarrierProxy | None: ...
    @hasHeatOutputCarrier.setter
    def hasHeatOutputCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def atHydrogenNode(self) -> HydrogenBusProxy | None: ...
    @atHydrogenNode.setter
    def atHydrogenNode(self, value: HydrogenBusProxy | str) -> None: ...
    @property
    def atFuelNode(self) -> NetworkNodeProxy | None: ...
    @atFuelNode.setter
    def atFuelNode(self, value: NetworkNodeProxy | str) -> None: ...
    @property
    def atElectricityNode(self) -> ElectricalBusProxy | None: ...
    @atElectricityNode.setter
    def atElectricityNode(self, value: ElectricalBusProxy | str) -> None: ...
    @property
    def atHeatNode(self) -> HeatBusProxy | None: ...
    @atHeatNode.setter
    def atHeatNode(self, value: HeatBusProxy | str) -> None: ...

class GasBusProxy(EntityProxy):
    spatial: GasBusSpatialProxy
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    latitude: float | None
    """Geographical latitude of the entity, expressed in decimal degrees. Used for spatial modelling, renewable resource assessment, and GIS-based visualisation. Unit: deg."""
    longitude: float | None
    """Geographical longitude of the entity, expressed in decimal degrees. Used for spatial modelling, renewable resource assessment, and GIS-based visualisation. Unit: deg."""
    elevation: float | None
    """Elevation of the entity above mean sea level, expressed in metres. Relevant for climate-adjusted performance modelling and topographic network studies. Unit: m."""
    nominal_pressure: float | None
    """Nominal operating pressure at a gas, hydrogen, or water Bus, expressed in bar (gauge). Defines the reference pressure level of the carrier domain at this node and is used for hydraulic network calculations and compressor/pump modelling. Unit: bar."""
    @property
    def belongsToGeographicalRegion(self) -> GeographicalRegionProxy | None: ...
    @belongsToGeographicalRegion.setter
    def belongsToGeographicalRegion(self, value: GeographicalRegionProxy | str) -> None: ...
    @property
    def belongsToCarrierDomain(self) -> CarrierDomainProxy: ...
    @belongsToCarrierDomain.setter
    def belongsToCarrierDomain(self, value: CarrierDomainProxy | str) -> None: ...

class GenerationUnitProxy(EntityProxy):
    capacity_expansion: GenerationUnitCapacityExpansionProxy
    dispatch: GenerationUnitDispatchProxy
    dynamics: GenerationUnitDynamicsProxy
    technical: GenerationUnitTechnicalProxy
    topology: GenerationUnitTopologyProxy
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    commissioning_year: int | None
    """Year in which the generation unit was first commissioned and became commercially operational. Instance-specific: determines actual age, real efficiency relative to nameplate, and remaining technical lifetime. Year alone is sufficient for planning and ageing models."""
    retrofit_date: datetime | None
    """Date of major upgrade or efficiency retrofit. Impacts operational efficiency, lifetime extension, and emission calculations. Unit: date."""
    retirement_date: datetime | None
    """Planned or actual date when the generator is permanently retired from service. Used for asset replacement planning and system expansion studies. Unit: date."""
    rated_voltage: float | None
    """Rated line-to-line terminal voltage of the deployed generation unit [kV]. Together with rated_apparent_power, defines the machine-specific impedance base. Unit: kV."""
    rated_apparent_power: float | None
    """Rated apparent power of the deployed generation unit [MVA]. Defines the machine-specific per-unit power base used with a linked DynamicMachineModelType. Unit: MVA."""
    generator_technology_type: str | None
    """Generation technology category when no GeneratorType library entity is referenced."""
    nominal_power_capacity: float | None
    """Maximum instantaneous power the asset, technology template, or conversion port can deliver or absorb, in MW. Defines operational limits for dispatch. Unit: MW."""
    minimum_generation: float | None
    """The minimum active power output that the generation entity can continuously produce while remaining in stable operation. This value represents the lower operational dispatch limit of the generator and is typically expressed in MW. Unit: MW."""
    maximum_generation: float | None
    """The maximum active power output that the generation entity can produce under normal operating conditions. This value represents the upper operational dispatch limit of the generator and is typically expressed in MW. Unit: MW."""
    variable_operating_cost: float | None
    """Marginal operating cost per unit of output (or throughput) used in dispatch optimisation. Unit: MU/MWh."""
    fixed_operating_cost: float | None
    """Fixed operation and maintenance (O&M) cost associated with the technology, typically expressed per year and per unit of installed capacity or per unit of technology. Covers costs that do not depend on energy production. Unit: MU/year, MU/(kW/year), MU/(MW/year), MU/unit."""
    energy_conversion_efficiency: float | None
    """Ratio of useful output energy to input energy, expressed as a fraction (0–1). Determines efficiency of energy conversion processes. Unit: fraction."""
    annual_resource_potential: float | None
    """Specifies the total annually available quantity of a resource or carrier that can be utilized, harvested, extracted, or converted by the represented entity under the assumptions of the associated scenario or resource representation. Unit: MWh/year."""
    dispatch_type: str | None
    """Dispatch classification of a generation technology: "dispatchable" — operator can choose output (thermal, hydro reservoir) "nondispatchable" — output bounded by external resource (wind, solar, RoR) "must_run" — must generate at minimum level (nuclear baseload, CHP)"""
    maximum_ramp_rate_up: float | None
    """The maximum increase in output power per unit time, typically expressed in kW/s or MW/min. Represents the upward operational flexibility of the asset (a generator ramping up, or a storage device discharging faster). Unit: %/h."""
    maximum_ramp_rate_down: float | None
    """The maximum percentage decrease in output power per unit time during ramp-down operations. Expressed as %/min or %/s, capturing the asset's downward operational flexibility (a generator ramping down, or a storage device changing its charging/discharging rate). Unit: %/h."""
    @property
    def hasTechnology(self) -> GeneratorTypeProxy | None: ...
    @hasTechnology.setter
    def hasTechnology(self, value: GeneratorTypeProxy | GeneratorTypeId) -> None: ...
    @property
    def hasInputResource(self) -> NaturalResourceProxy | None: ...
    @hasInputResource.setter
    def hasInputResource(self, value: NaturalResourceProxy | NaturalResourceId) -> None: ...
    @property
    def hasInputCarrier(self) -> CarrierProxy | None: ...
    @hasInputCarrier.setter
    def hasInputCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def hasOutputCarrier(self) -> CarrierProxy | None: ...
    @hasOutputCarrier.setter
    def hasOutputCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def hasAvailabilityProfile(self) -> ProfileProxy | None: ...
    @hasAvailabilityProfile.setter
    def hasAvailabilityProfile(self, value: ProfileProxy | str) -> None: ...
    @property
    def atNode(self) -> NetworkNodeProxy | None: ...
    @atNode.setter
    def atNode(self, value: NetworkNodeProxy | str) -> None: ...
    @property
    def belongsToGeographicalRegion(self) -> GeographicalRegionProxy | None: ...
    @belongsToGeographicalRegion.setter
    def belongsToGeographicalRegion(self, value: GeographicalRegionProxy | str) -> None: ...

class GeneratorTypeProxy(EntityProxy):
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    energy_conversion_efficiency: float | None
    """Ratio of useful output energy to input energy, expressed as a fraction (0–1). Determines efficiency of energy conversion processes. Unit: fraction."""
    dispatch_type: str | None
    """Dispatch classification of a generation technology: "dispatchable" — operator can choose output (thermal, hydro reservoir) "nondispatchable" — output bounded by external resource (wind, solar, RoR) "must_run" — must generate at minimum level (nuclear baseload, CHP)"""
    variable_operating_cost: float | None
    """Marginal operating cost per unit of output (or throughput) used in dispatch optimisation. Unit: MU/MWh."""
    fixed_operating_cost: float | None
    """Fixed operation and maintenance (O&M) cost associated with the technology, typically expressed per year and per unit of installed capacity or per unit of technology. Covers costs that do not depend on energy production. Unit: MU/year, MU/(kW/year), MU/(MW/year), MU/unit."""
    investment_cost: float | None
    """Overnight investment cost of the technology per unit of installed capacity or per unit, depending on the modeling convention. Used together with technical_lifetime and discount_rate for annualized cost calculations. Unit: MU/kW, MU/MW, MU/unit."""
    technical_lifetime: float | None
    """Technical lifetime of the asset in years. Unit: years."""
    discount_rate: float | None
    """Discount rate applied to investment and cost streams associated with this technology, expressed as a fraction between 0 and 1 (e.g. 0.03 for 3%). May override a global discount rate defined at the Energy System Model level. Unit: fraction."""
    salvage_fraction_value: float | None
    """Fraction of the original investment value that is recovered as salvage at the end of the planning horizon, expressed as a fraction between 0 and 1. Used for partial lifetime treatment when the technology lifetime extends beyond the modeled period. Unit: fraction."""
    maximum_ramp_rate_up: float | None
    """The maximum increase in output power per unit time, typically expressed in kW/s or MW/min. Represents the upward operational flexibility of the asset (a generator ramping up, or a storage device discharging faster). Unit: %/h."""
    maximum_ramp_rate_down: float | None
    """The maximum percentage decrease in output power per unit time during ramp-down operations. Expressed as %/min or %/s, capturing the asset's downward operational flexibility (a generator ramping down, or a storage device changing its charging/discharging rate). Unit: %/h."""
    minimum_up_time: float | None
    """Minimum number of hours a unit must remain online once started. Used in unit commitment models. Unit: h."""
    minimum_down_time: float | None
    """Minimum number of hours a unit must remain offline after shutdown. Used in unit commitment models. Unit: h."""
    hot_start_cost: float | None
    """Cost incurred to restart a generator that has been recently offline (hot state), expressed in monitary units. Reflects fuel and operational overhead. Unit: MU."""
    cold_start_cost: float | None
    """Cost incurred to restart a generator that has been offline for a long period (cold state), expressed in MU. Usually higher than hot start due to additional operational procedures. Unit: MU."""
    ramping_cost_increase: float | None
    """The cost associated with increasing output power, expressed in MU/MW or MU/MW/min. Used in dispatch optimisation to represent wear, thermal cycling, or operational penalties for fast upward ramping. Unit: MU/MW."""
    ramping_cost_decrease: float | None
    """The cost associated with reducing output power or reducing charging rate, expressed in MonetaryUnits/MW or MonetaryUnits/MW/min. Represents operational constraints or efficiency penalties during ramp-down."""
    generator_technology_type: str | None
    """Generation technology category when no GeneratorType library entity is referenced."""
    comment: str | None
    """Optional comment/notes."""
    economic_lifetime: float | None
    """Economic/depreciation lifetime of the asset in years. Unit: years."""
    co2_emission_factor: float | None
    """Direct CO₂ emissions per unit of electrical output [tCO₂ / MWh_el]. For fuel-based generators this is fuel_co2_intensity / efficiency. Unit: tCO2/MWh."""
    fuel_consumption_rate: float | None
    """Fuel input per unit of electrical output [MWh_fuel / MWh_el], equal to 1 / energy_conversion_efficiency."""
    @property
    def hasInputCarrier(self) -> CarrierProxy | None: ...
    @hasInputCarrier.setter
    def hasInputCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def hasInputResource(self) -> NaturalResourceProxy | None: ...
    @hasInputResource.setter
    def hasInputResource(self, value: NaturalResourceProxy | NaturalResourceId) -> None: ...
    @property
    def hasOutputCarrier(self) -> CarrierProxy | None: ...
    @hasOutputCarrier.setter
    def hasOutputCarrier(self, value: CarrierProxy | CarrierId) -> None: ...

class GenericConversionUnitProxy(EntityProxy):
    capacity_expansion: GenericConversionUnitCapacityExpansionProxy
    dispatch: GenericConversionUnitDispatchProxy
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    commissioning_year: int | None
    """Year in which the generation unit was first commissioned and became commercially operational. Instance-specific: determines actual age, real efficiency relative to nameplate, and remaining technical lifetime. Year alone is sufficient for planning and ageing models."""
    retrofit_date: datetime | None
    """Date of major upgrade or efficiency retrofit. Impacts operational efficiency, lifetime extension, and emission calculations. Unit: date."""
    retirement_date: datetime | None
    """Planned or actual date when the generator is permanently retired from service. Used for asset replacement planning and system expansion studies. Unit: date."""
    nominal_power_capacity: float | None
    """Maximum instantaneous power the asset, technology template, or conversion port can deliver or absorb, in MW. Defines operational limits for dispatch. Unit: MW."""
    @property
    def referencePort(self) -> ConversionPortProxy | None: ...
    @referencePort.setter
    def referencePort(self, value: ConversionPortProxy | str) -> None: ...

class GenericInterconnectorProxy(EntityProxy):
    capacity_expansion: GenericInterconnectorCapacityExpansionProxy
    dispatch: GenericInterconnectorDispatchProxy
    power_flow: GenericInterconnectorPowerFlowProxy
    topology: GenericInterconnectorTopologyProxy
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    commissioning_year: int | None
    """Year in which the generation unit was first commissioned and became commercially operational. Instance-specific: determines actual age, real efficiency relative to nameplate, and remaining technical lifetime. Year alone is sufficient for planning and ageing models."""
    retrofit_date: datetime | None
    """Date of major upgrade or efficiency retrofit. Impacts operational efficiency, lifetime extension, and emission calculations. Unit: date."""
    retirement_date: datetime | None
    """Planned or actual date when the generator is permanently retired from service. Used for asset replacement planning and system expansion studies. Unit: date."""
    from_switch_closed: bool | None
    """Boolean indicating whether the breaker at the from-end of the branch is closed (true = connected, false = disconnected). Used in contingency and outage modelling."""
    to_switch_closed: bool | None
    """Boolean indicating whether the breaker at the to-end of the branch is closed (true = connected, false = disconnected). Used in contingency and outage modelling."""
    maximum_power_flow_from_to: float | None
    """Maximum power flow in the direction from node 1 to node 2, used for asymmetric capacity limits (e.g., NTC interconnectors). Unit: MW."""
    maximum_power_flow_to_from: float | None
    """Maximum power flow in the direction from node 2 to node 1, used for asymmetric capacity limits (e.g., NTC interconnectors). Unit: MW."""
    @property
    def fromNode(self) -> NetworkNodeProxy | None: ...
    @fromNode.setter
    def fromNode(self, value: NetworkNodeProxy | str) -> None: ...
    @property
    def toNode(self) -> NetworkNodeProxy | None: ...
    @toNode.setter
    def toNode(self, value: NetworkNodeProxy | str) -> None: ...
    @property
    def fromRegion(self) -> GeographicalRegionProxy | None: ...
    @fromRegion.setter
    def fromRegion(self, value: GeographicalRegionProxy | str) -> None: ...
    @property
    def toRegion(self) -> GeographicalRegionProxy | None: ...
    @toRegion.setter
    def toRegion(self, value: GeographicalRegionProxy | str) -> None: ...

class GeographicalRegionProxy(EntityProxy):
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    region_level: str | None
    """Administrative / statistical level of a GeographicalRegion: country (ISO / NUTS 0), nuts1, nuts2, nuts3, or other custom regions."""
    nuts_code: str | None
    """Official NUTS code for the region when region_level is country/nuts1/nuts2/nuts3 (e.g. CH, CH0, CH01, CH011). Empty for non-NUTS custom regions."""
    iso_country_code: str | None
    """ISO 3166-1 alpha-2 country code associated with the region (e.g. CH, DE). For NUTS regions this is typically the two-letter country prefix (with EL→GR and UK→GB remapping applied where relevant)."""
    @property
    def isSubRegionOf(self) -> GeographicalRegionProxy | None: ...
    @isSubRegionOf.setter
    def isSubRegionOf(self, value: GeographicalRegionProxy | str) -> None: ...

class HVDCLinkProxy(EntityProxy):
    capacity_expansion: HVDCLinkCapacityExpansionProxy
    dispatch: HVDCLinkDispatchProxy
    power_flow: HVDCLinkPowerFlowProxy
    topology: HVDCLinkTopologyProxy
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    commissioning_year: int | None
    """Year in which the generation unit was first commissioned and became commercially operational. Instance-specific: determines actual age, real efficiency relative to nameplate, and remaining technical lifetime. Year alone is sufficient for planning and ageing models."""
    retrofit_date: datetime | None
    """Date of major upgrade or efficiency retrofit. Impacts operational efficiency, lifetime extension, and emission calculations. Unit: date."""
    retirement_date: datetime | None
    """Planned or actual date when the generator is permanently retired from service. Used for asset replacement planning and system expansion studies. Unit: date."""
    from_switch_closed: bool | None
    """Boolean indicating whether the breaker at the from-end of the branch is closed (true = connected, false = disconnected). Used in contingency and outage modelling."""
    to_switch_closed: bool | None
    """Boolean indicating whether the breaker at the to-end of the branch is closed (true = connected, false = disconnected). Used in contingency and outage modelling."""
    max_flow: float | None
    """Maximum carrier flow permitted through a branch or interconnector without violating operational limits, expressed in MW (power) or the appropriate flow unit for the carrier. Unit: MW."""
    variable_operating_cost: float | None
    """Marginal operating cost per unit of output (or throughput) used in dispatch optimisation. Unit: MU/MWh."""
    @property
    def fromNode(self) -> ElectricalBusProxy | None: ...
    @fromNode.setter
    def fromNode(self, value: ElectricalBusProxy | str) -> None: ...
    @property
    def toNode(self) -> ElectricalBusProxy | None: ...
    @toNode.setter
    def toNode(self, value: ElectricalBusProxy | str) -> None: ...

class HeatBusProxy(EntityProxy):
    spatial: HeatBusSpatialProxy
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    latitude: float | None
    """Geographical latitude of the entity, expressed in decimal degrees. Used for spatial modelling, renewable resource assessment, and GIS-based visualisation. Unit: deg."""
    longitude: float | None
    """Geographical longitude of the entity, expressed in decimal degrees. Used for spatial modelling, renewable resource assessment, and GIS-based visualisation. Unit: deg."""
    elevation: float | None
    """Elevation of the entity above mean sea level, expressed in metres. Relevant for climate-adjusted performance modelling and topographic network studies. Unit: m."""
    nominal_temperature: float | None
    """Nominal supply temperature at a heat network Bus, expressed in degrees Celsius. Defines the reference temperature of the heat carrier at this node and is used for thermal network flow calculations and heat exchanger modelling. Unit: degC."""
    nominal_pressure: float | None
    """Nominal operating pressure at a gas, hydrogen, or water Bus, expressed in bar (gauge). Defines the reference pressure level of the carrier domain at this node and is used for hydraulic network calculations and compressor/pump modelling. Unit: bar."""
    @property
    def belongsToGeographicalRegion(self) -> GeographicalRegionProxy | None: ...
    @belongsToGeographicalRegion.setter
    def belongsToGeographicalRegion(self, value: GeographicalRegionProxy | str) -> None: ...
    @property
    def belongsToCarrierDomain(self) -> CarrierDomainProxy: ...
    @belongsToCarrierDomain.setter
    def belongsToCarrierDomain(self, value: CarrierDomainProxy | str) -> None: ...

class HeatPumpUnitProxy(EntityProxy):
    capacity_expansion: HeatPumpUnitCapacityExpansionProxy
    dispatch: HeatPumpUnitDispatchProxy
    technical: HeatPumpUnitTechnicalProxy
    topology: HeatPumpUnitTopologyProxy
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    commissioning_year: int | None
    """Year in which the generation unit was first commissioned and became commercially operational. Instance-specific: determines actual age, real efficiency relative to nameplate, and remaining technical lifetime. Year alone is sufficient for planning and ageing models."""
    retrofit_date: datetime | None
    """Date of major upgrade or efficiency retrofit. Impacts operational efficiency, lifetime extension, and emission calculations. Unit: date."""
    retirement_date: datetime | None
    """Planned or actual date when the generator is permanently retired from service. Used for asset replacement planning and system expansion studies. Unit: date."""
    coefficient_of_performance: float | None
    """Ratio of useful heat output to electrical energy input for a heat pump (COP). Values greater than 1 are typical; not constrained to the unit interval."""
    nominal_thermal_power_capacity: float | None
    """Maximum useful heat the conversion unit or its technology template can deliver, in MW. Applies to CHPUnit, HeatPumpUnit, BoilerUnit, and FuelCellUnit. Unit: MW."""
    nominal_electrical_power_capacity: float | None
    """Maximum electrical power (output or input rating) of a compact ConversionUnit such as CHPUnit, FuelCellUnit, HeatPumpUnit, or ElectrolyserUnit. Unit: MW."""
    minimum_load: float | None
    """Minimum stable operating load as a fraction of nominal electrical power. Unit: fraction."""
    maximum_ramp_rate_up: float | None
    """The maximum increase in output power per unit time, typically expressed in kW/s or MW/min. Represents the upward operational flexibility of the asset (a generator ramping up, or a storage device discharging faster). Unit: %/h."""
    maximum_ramp_rate_down: float | None
    """The maximum percentage decrease in output power per unit time during ramp-down operations. Expressed as %/min or %/s, capturing the asset's downward operational flexibility (a generator ramping down, or a storage device changing its charging/discharging rate). Unit: %/h."""
    variable_operating_cost: float | None
    """Marginal operating cost per unit of output (or throughput) used in dispatch optimisation. Unit: MU/MWh."""
    fixed_operating_cost: float | None
    """Fixed operation and maintenance (O&M) cost associated with the technology, typically expressed per year and per unit of installed capacity or per unit of technology. Covers costs that do not depend on energy production. Unit: MU/year, MU/(kW/year), MU/(MW/year), MU/unit."""
    @property
    def hasInputCarrier(self) -> CarrierProxy | None: ...
    @hasInputCarrier.setter
    def hasInputCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def hasHeatOutputCarrier(self) -> CarrierProxy | None: ...
    @hasHeatOutputCarrier.setter
    def hasHeatOutputCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def atElectricityNode(self) -> ElectricalBusProxy | None: ...
    @atElectricityNode.setter
    def atElectricityNode(self, value: ElectricalBusProxy | str) -> None: ...
    @property
    def atHeatNode(self) -> HeatBusProxy | None: ...
    @atHeatNode.setter
    def atHeatNode(self, value: HeatBusProxy | str) -> None: ...

class HydroGenerationUnitProxy(EntityProxy):
    capacity_expansion: HydroGenerationUnitCapacityExpansionProxy
    dispatch: HydroGenerationUnitDispatchProxy
    dynamics: HydroGenerationUnitDynamicsProxy
    technical: HydroGenerationUnitTechnicalProxy
    topology: HydroGenerationUnitTopologyProxy
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    commissioning_year: int | None
    """Year in which the generation unit was first commissioned and became commercially operational. Instance-specific: determines actual age, real efficiency relative to nameplate, and remaining technical lifetime. Year alone is sufficient for planning and ageing models."""
    retrofit_date: datetime | None
    """Date of major upgrade or efficiency retrofit. Impacts operational efficiency, lifetime extension, and emission calculations. Unit: date."""
    retirement_date: datetime | None
    """Planned or actual date when the generator is permanently retired from service. Used for asset replacement planning and system expansion studies. Unit: date."""
    rated_voltage: float | None
    """Rated line-to-line terminal voltage of the deployed generation unit [kV]. Together with rated_apparent_power, defines the machine-specific impedance base. Unit: kV."""
    rated_apparent_power: float | None
    """Rated apparent power of the deployed generation unit [MVA]. Defines the machine-specific per-unit power base used with a linked DynamicMachineModelType. Unit: MVA."""
    generator_technology_type: str | None
    """Generation technology category when no GeneratorType library entity is referenced."""
    nominal_power_capacity: float | None
    """Maximum instantaneous power the asset, technology template, or conversion port can deliver or absorb, in MW. Defines operational limits for dispatch. Unit: MW."""
    minimum_generation: float | None
    """The minimum active power output that the generation entity can continuously produce while remaining in stable operation. This value represents the lower operational dispatch limit of the generator and is typically expressed in MW. Unit: MW."""
    maximum_generation: float | None
    """The maximum active power output that the generation entity can produce under normal operating conditions. This value represents the upper operational dispatch limit of the generator and is typically expressed in MW. Unit: MW."""
    variable_operating_cost: float | None
    """Marginal operating cost per unit of output (or throughput) used in dispatch optimisation. Unit: MU/MWh."""
    fixed_operating_cost: float | None
    """Fixed operation and maintenance (O&M) cost associated with the technology, typically expressed per year and per unit of installed capacity or per unit of technology. Covers costs that do not depend on energy production. Unit: MU/year, MU/(kW/year), MU/(MW/year), MU/unit."""
    energy_conversion_efficiency: float | None
    """Ratio of useful output energy to input energy, expressed as a fraction (0–1). Determines efficiency of energy conversion processes. Unit: fraction."""
    annual_resource_potential: float | None
    """Specifies the total annually available quantity of a resource or carrier that can be utilized, harvested, extracted, or converted by the represented entity under the assumptions of the associated scenario or resource representation. Unit: MWh/year."""
    dispatch_type: str | None
    """Dispatch classification of a generation technology: "dispatchable" — operator can choose output (thermal, hydro reservoir) "nondispatchable" — output bounded by external resource (wind, solar, RoR) "must_run" — must generate at minimum level (nuclear baseload, CHP)"""
    maximum_ramp_rate_up: float | None
    """The maximum increase in output power per unit time, typically expressed in kW/s or MW/min. Represents the upward operational flexibility of the asset (a generator ramping up, or a storage device discharging faster). Unit: %/h."""
    maximum_ramp_rate_down: float | None
    """The maximum percentage decrease in output power per unit time during ramp-down operations. Expressed as %/min or %/s, capturing the asset's downward operational flexibility (a generator ramping down, or a storage device changing its charging/discharging rate). Unit: %/h."""
    hydraulic_head: float | None
    """Net hydraulic head available at the turbine under design conditions. Determines the theoretical power output together with flow rate and turbine efficiency. Instance-specific: depends on reservoir level and tailwater. Unit: m."""
    turbine_type: str | None
    """Hydro turbine family (Francis, Kaplan, Pelton, …) for a HydroGenerationUnit."""
    hydro_machine_kind: str | None
    """Hydro machine class for dispatch: turbine = generation-only; pump = pump-only (consumes electricity to move water); reversible = pump-turbine that can operate in both modes. Distinct from turbine_type (Francis/Kaplan/…) and GeneratorType."""
    turbine_efficiency: float | None
    """The fraction of hydraulic energy converted into useful electrical output by the turbine or turbine-generator set, expressed as a value between 0 and 1. Applies to HydroGenerationUnit and avoids storage-discharge semantics. Unit: fraction."""
    maximum_pumping_power: float | None
    """Maximum electrical power consumed during pumping operation [MW]. May differ from the turbine generation capacity in ternary or quaternary configurations. Only relevant for phs_closed_loop and phs_open_loop. Unit: MW."""
    pumping_efficiency: float | None
    """Pumping efficiency of a HydroGenerationUnit (electrical energy in → hydraulic energy stored). Distinct from charging_efficiency on battery-style StorageUnit. Unit: pu."""
    @property
    def hasTechnology(self) -> GeneratorTypeProxy | None: ...
    @hasTechnology.setter
    def hasTechnology(self, value: GeneratorTypeProxy | GeneratorTypeId) -> None: ...
    @property
    def hasInputResource(self) -> NaturalResourceProxy | None: ...
    @hasInputResource.setter
    def hasInputResource(self, value: NaturalResourceProxy | NaturalResourceId) -> None: ...
    @property
    def hasInputCarrier(self) -> CarrierProxy | None: ...
    @hasInputCarrier.setter
    def hasInputCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def hasOutputCarrier(self) -> CarrierProxy | None: ...
    @hasOutputCarrier.setter
    def hasOutputCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def hasAvailabilityProfile(self) -> ProfileProxy | None: ...
    @hasAvailabilityProfile.setter
    def hasAvailabilityProfile(self, value: ProfileProxy | str) -> None: ...
    @property
    def atNode(self) -> NetworkNodeProxy | None: ...
    @atNode.setter
    def atNode(self, value: NetworkNodeProxy | str) -> None: ...
    @property
    def belongsToGeographicalRegion(self) -> GeographicalRegionProxy | None: ...
    @belongsToGeographicalRegion.setter
    def belongsToGeographicalRegion(self, value: GeographicalRegionProxy | str) -> None: ...
    @property
    def drawsFromHydroReservoir(self) -> list[HydroReservoirProxy] | None: ...
    @drawsFromHydroReservoir.setter
    def drawsFromHydroReservoir(self, value: Iterable[HydroReservoirProxy | str]) -> None: ...
    @property
    def releasesToHydroReservoir(self) -> HydroReservoirProxy | None: ...
    @releasesToHydroReservoir.setter
    def releasesToHydroReservoir(self, value: HydroReservoirProxy | str) -> None: ...

class HydroReservoirProxy(EntityProxy):
    capacity_expansion: HydroReservoirCapacityExpansionProxy
    dispatch: HydroReservoirDispatchProxy
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    commissioning_year: int | None
    """Year in which the generation unit was first commissioned and became commercially operational. Instance-specific: determines actual age, real efficiency relative to nameplate, and remaining technical lifetime. Year alone is sufficient for planning and ageing models."""
    retrofit_date: datetime | None
    """Date of major upgrade or efficiency retrofit. Impacts operational efficiency, lifetime extension, and emission calculations. Unit: date."""
    retirement_date: datetime | None
    """Planned or actual date when the generator is permanently retired from service. Used for asset replacement planning and system expansion studies. Unit: date."""
    energy_storage_capacity: float | None
    """Maximum net energy or storage medium volume that can be stored and subsequently released under defined operating conditions, expressed as the difference between maximum and minimum allowable state of charge. Use MWh for energy-equivalent storage models and m3 for reservoir water-volume models. Unit: MWh, m3."""
    annual_natural_inflow_energy: float | None
    """Total natural inflow received by a storage asset over one year. Used as the scaling factor when converting a normalised inflow profile (as_normalized_annual_energy) to absolute hourly inflow values in dispatch optimisation models. Unit: MWh/year."""
    @property
    def storesCarrier(self) -> CarrierProxy | None: ...
    @storesCarrier.setter
    def storesCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def storesResource(self) -> NaturalResourceProxy | None: ...
    @storesResource.setter
    def storesResource(self, value: NaturalResourceProxy | NaturalResourceId) -> None: ...
    @property
    def hasNaturalInflowProfile(self) -> ProfileProxy | None: ...
    @hasNaturalInflowProfile.setter
    def hasNaturalInflowProfile(self, value: ProfileProxy | str) -> None: ...

class HydrogenBusProxy(EntityProxy):
    spatial: HydrogenBusSpatialProxy
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    latitude: float | None
    """Geographical latitude of the entity, expressed in decimal degrees. Used for spatial modelling, renewable resource assessment, and GIS-based visualisation. Unit: deg."""
    longitude: float | None
    """Geographical longitude of the entity, expressed in decimal degrees. Used for spatial modelling, renewable resource assessment, and GIS-based visualisation. Unit: deg."""
    elevation: float | None
    """Elevation of the entity above mean sea level, expressed in metres. Relevant for climate-adjusted performance modelling and topographic network studies. Unit: m."""
    nominal_pressure: float | None
    """Nominal operating pressure at a gas, hydrogen, or water Bus, expressed in bar (gauge). Defines the reference pressure level of the carrier domain at this node and is used for hydraulic network calculations and compressor/pump modelling. Unit: bar."""
    @property
    def belongsToGeographicalRegion(self) -> GeographicalRegionProxy | None: ...
    @belongsToGeographicalRegion.setter
    def belongsToGeographicalRegion(self, value: GeographicalRegionProxy | str) -> None: ...
    @property
    def belongsToCarrierDomain(self) -> CarrierDomainProxy: ...
    @belongsToCarrierDomain.setter
    def belongsToCarrierDomain(self, value: CarrierDomainProxy | str) -> None: ...

class NaturalResourceProxy(EntityProxy):
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    resource_group: str | None
    """Broad group of a NaturalResource."""
    resource_type: str | None
    """Natural-resource category (wind, solar, hydro inflow, …)."""
    natural_resource_unit: str | None
    """Canonical physical unit used when the resource is represented as an absolute quantity or rate."""

class NetworkNodeProxy(EntityProxy):
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    latitude: float | None
    """Geographical latitude of the entity, expressed in decimal degrees. Used for spatial modelling, renewable resource assessment, and GIS-based visualisation. Unit: deg."""
    longitude: float | None
    """Geographical longitude of the entity, expressed in decimal degrees. Used for spatial modelling, renewable resource assessment, and GIS-based visualisation. Unit: deg."""
    elevation: float | None
    """Elevation of the entity above mean sea level, expressed in metres. Relevant for climate-adjusted performance modelling and topographic network studies. Unit: m."""
    @property
    def belongsToGeographicalRegion(self) -> GeographicalRegionProxy | None: ...
    @belongsToGeographicalRegion.setter
    def belongsToGeographicalRegion(self, value: GeographicalRegionProxy | str) -> None: ...
    @property
    def belongsToCarrierDomain(self) -> CarrierDomainProxy: ...
    @belongsToCarrierDomain.setter
    def belongsToCarrierDomain(self, value: CarrierDomainProxy | CarrierDomainId) -> None: ...

class PortProxy(EntityProxy):
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""

class ProfileProxy(EntityProxy):
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    profile_type: str
    """How profile samples are interpreted (absolute SI, capacity factor, or normalized annual energy)."""
    profile_unit: str | None
    """SI unit of the profile values. Only meaningful for as_SI profiles (e.g. "MW", "MWh", "m3/s"). Dimensionless profiles (capacity factor and normalized annual energy) should leave this blank or set it to "pu" (per unit)."""
    data_reference: str
    """Internal HDF5 path identifying the numeric payload for this profile, formatted as "/profiles/<entity_id>" (e.g. "/profiles/profile.demand.electricity.at00"). The values dataset at this path contains a float64 array of length equal to the referenced TimestampSeries length. This attribute is the bridge between the YAML entity store and the HDF5 data store."""
    @property
    def hasTimestampSeries(self) -> TimestampSeriesProxy: ...
    @hasTimestampSeries.setter
    def hasTimestampSeries(self, value: TimestampSeriesProxy | str) -> None: ...

class SemanticEntityProxy(EntityProxy):
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""

class SolarGenerationUnitProxy(EntityProxy):
    capacity_expansion: SolarGenerationUnitCapacityExpansionProxy
    dispatch: SolarGenerationUnitDispatchProxy
    dynamics: SolarGenerationUnitDynamicsProxy
    technical: SolarGenerationUnitTechnicalProxy
    topology: SolarGenerationUnitTopologyProxy
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    commissioning_year: int | None
    """Year in which the generation unit was first commissioned and became commercially operational. Instance-specific: determines actual age, real efficiency relative to nameplate, and remaining technical lifetime. Year alone is sufficient for planning and ageing models."""
    retrofit_date: datetime | None
    """Date of major upgrade or efficiency retrofit. Impacts operational efficiency, lifetime extension, and emission calculations. Unit: date."""
    retirement_date: datetime | None
    """Planned or actual date when the generator is permanently retired from service. Used for asset replacement planning and system expansion studies. Unit: date."""
    rated_voltage: float | None
    """Rated line-to-line terminal voltage of the deployed generation unit [kV]. Together with rated_apparent_power, defines the machine-specific impedance base. Unit: kV."""
    rated_apparent_power: float | None
    """Rated apparent power of the deployed generation unit [MVA]. Defines the machine-specific per-unit power base used with a linked DynamicMachineModelType. Unit: MVA."""
    generator_technology_type: str | None
    """Generation technology category when no GeneratorType library entity is referenced."""
    nominal_power_capacity: float | None
    """Maximum instantaneous power the asset, technology template, or conversion port can deliver or absorb, in MW. Defines operational limits for dispatch. Unit: MW."""
    minimum_generation: float | None
    """The minimum active power output that the generation entity can continuously produce while remaining in stable operation. This value represents the lower operational dispatch limit of the generator and is typically expressed in MW. Unit: MW."""
    maximum_generation: float | None
    """The maximum active power output that the generation entity can produce under normal operating conditions. This value represents the upper operational dispatch limit of the generator and is typically expressed in MW. Unit: MW."""
    variable_operating_cost: float | None
    """Marginal operating cost per unit of output (or throughput) used in dispatch optimisation. Unit: MU/MWh."""
    fixed_operating_cost: float | None
    """Fixed operation and maintenance (O&M) cost associated with the technology, typically expressed per year and per unit of installed capacity or per unit of technology. Covers costs that do not depend on energy production. Unit: MU/year, MU/(kW/year), MU/(MW/year), MU/unit."""
    energy_conversion_efficiency: float | None
    """Ratio of useful output energy to input energy, expressed as a fraction (0–1). Determines efficiency of energy conversion processes. Unit: fraction."""
    annual_resource_potential: float | None
    """Specifies the total annually available quantity of a resource or carrier that can be utilized, harvested, extracted, or converted by the represented entity under the assumptions of the associated scenario or resource representation. Unit: MWh/year."""
    dispatch_type: str | None
    """Dispatch classification of a generation technology: "dispatchable" — operator can choose output (thermal, hydro reservoir) "nondispatchable" — output bounded by external resource (wind, solar, RoR) "must_run" — must generate at minimum level (nuclear baseload, CHP)"""
    maximum_ramp_rate_up: float | None
    """The maximum increase in output power per unit time, typically expressed in kW/s or MW/min. Represents the upward operational flexibility of the asset (a generator ramping up, or a storage device discharging faster). Unit: %/h."""
    maximum_ramp_rate_down: float | None
    """The maximum percentage decrease in output power per unit time during ramp-down operations. Expressed as %/min or %/s, capturing the asset's downward operational flexibility (a generator ramping down, or a storage device changing its charging/discharging rate). Unit: %/h."""
    tilt_angle: float | None
    """Tilt angle of the solar panels relative to the horizontal plane. 0° = horizontal, 90° = vertical. Optimal value depends on latitude and tracking system. Instance-specific. Unit: deg."""
    azimuth_angle: float | None
    """Azimuth orientation of the solar panels. Measured clockwise from north: 0° = north, 90° = east, 180° = south, 270° = west. 180° (south-facing) is optimal in the northern hemisphere. Unit: deg."""
    tracking_type: str | None
    """Tracking system of the solar installation. Fixed systems have no moving parts. Single-axis trackers follow the sun east-west. Dual-axis trackers follow both elevation and azimuth. Allowed values: fixed, single_axis, dual_axis."""
    panel_technology: str | None
    """Photovoltaic cell technology or solar thermal technology type. Determines efficiency, degradation rate, and temperature coefficient. Allowed values: monocrystalline, polycrystalline, thin_film, csp."""
    @property
    def hasTechnology(self) -> GeneratorTypeProxy | None: ...
    @hasTechnology.setter
    def hasTechnology(self, value: GeneratorTypeProxy | GeneratorTypeId) -> None: ...
    @property
    def hasInputResource(self) -> NaturalResourceProxy | None: ...
    @hasInputResource.setter
    def hasInputResource(self, value: NaturalResourceProxy | NaturalResourceId) -> None: ...
    @property
    def hasInputCarrier(self) -> CarrierProxy | None: ...
    @hasInputCarrier.setter
    def hasInputCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def hasOutputCarrier(self) -> CarrierProxy | None: ...
    @hasOutputCarrier.setter
    def hasOutputCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def hasAvailabilityProfile(self) -> ProfileProxy | None: ...
    @hasAvailabilityProfile.setter
    def hasAvailabilityProfile(self, value: ProfileProxy | str) -> None: ...
    @property
    def atNode(self) -> NetworkNodeProxy | None: ...
    @atNode.setter
    def atNode(self, value: NetworkNodeProxy | str) -> None: ...
    @property
    def belongsToGeographicalRegion(self) -> GeographicalRegionProxy | None: ...
    @belongsToGeographicalRegion.setter
    def belongsToGeographicalRegion(self, value: GeographicalRegionProxy | str) -> None: ...

class StorageTypeProxy(EntityProxy):
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    energy_conversion_efficiency: float | None
    """Ratio of useful output energy to input energy, expressed as a fraction (0–1). Determines efficiency of energy conversion processes. Unit: fraction."""
    dispatch_type: str | None
    """Dispatch classification of a generation technology: "dispatchable" — operator can choose output (thermal, hydro reservoir) "nondispatchable" — output bounded by external resource (wind, solar, RoR) "must_run" — must generate at minimum level (nuclear baseload, CHP)"""
    variable_operating_cost: float | None
    """Marginal operating cost per unit of output (or throughput) used in dispatch optimisation. Unit: MU/MWh."""
    fixed_operating_cost: float | None
    """Fixed operation and maintenance (O&M) cost associated with the technology, typically expressed per year and per unit of installed capacity or per unit of technology. Covers costs that do not depend on energy production. Unit: MU/year, MU/(kW/year), MU/(MW/year), MU/unit."""
    investment_cost: float | None
    """Overnight investment cost of the technology per unit of installed capacity or per unit, depending on the modeling convention. Used together with technical_lifetime and discount_rate for annualized cost calculations. Unit: MU/kW, MU/MW, MU/unit."""
    technical_lifetime: float | None
    """Technical lifetime of the asset in years. Unit: years."""
    discount_rate: float | None
    """Discount rate applied to investment and cost streams associated with this technology, expressed as a fraction between 0 and 1 (e.g. 0.03 for 3%). May override a global discount rate defined at the Energy System Model level. Unit: fraction."""
    salvage_fraction_value: float | None
    """Fraction of the original investment value that is recovered as salvage at the end of the planning horizon, expressed as a fraction between 0 and 1. Used for partial lifetime treatment when the technology lifetime extends beyond the modeled period. Unit: fraction."""
    maximum_ramp_rate_up: float | None
    """The maximum increase in output power per unit time, typically expressed in kW/s or MW/min. Represents the upward operational flexibility of the asset (a generator ramping up, or a storage device discharging faster). Unit: %/h."""
    maximum_ramp_rate_down: float | None
    """The maximum percentage decrease in output power per unit time during ramp-down operations. Expressed as %/min or %/s, capturing the asset's downward operational flexibility (a generator ramping down, or a storage device changing its charging/discharging rate). Unit: %/h."""
    minimum_up_time: float | None
    """Minimum number of hours a unit must remain online once started. Used in unit commitment models. Unit: h."""
    minimum_down_time: float | None
    """Minimum number of hours a unit must remain offline after shutdown. Used in unit commitment models. Unit: h."""
    hot_start_cost: float | None
    """Cost incurred to restart a generator that has been recently offline (hot state), expressed in monitary units. Reflects fuel and operational overhead. Unit: MU."""
    cold_start_cost: float | None
    """Cost incurred to restart a generator that has been offline for a long period (cold state), expressed in MU. Usually higher than hot start due to additional operational procedures. Unit: MU."""
    ramping_cost_increase: float | None
    """The cost associated with increasing output power, expressed in MU/MW or MU/MW/min. Used in dispatch optimisation to represent wear, thermal cycling, or operational penalties for fast upward ramping. Unit: MU/MW."""
    ramping_cost_decrease: float | None
    """The cost associated with reducing output power or reducing charging rate, expressed in MonetaryUnits/MW or MonetaryUnits/MW/min. Represents operational constraints or efficiency penalties during ramp-down."""
    generator_technology_type: str | None
    """Generation technology category when no GeneratorType library entity is referenced."""
    comment: str | None
    """Optional comment/notes."""
    energy_storage_capacity: float | None
    """Maximum net energy or storage medium volume that can be stored and subsequently released under defined operating conditions, expressed as the difference between maximum and minimum allowable state of charge. Use MWh for energy-equivalent storage models and m3 for reservoir water-volume models. Unit: MWh, m3."""
    nominal_power_capacity: float | None
    """Maximum instantaneous power the asset, technology template, or conversion port can deliver or absorb, in MW. Defines operational limits for dispatch. Unit: MW."""
    charging_efficiency: float | None
    """The fraction of input energy that is successfully stored during the charging process, expressed as a value between 0 and 1. Accounts for losses in power electronics, conversion stages, and internal storage mechanisms. Unit: fraction."""
    discharging_efficiency: float | None
    """The fraction of stored energy that can be delivered as useful output during the discharging process, expressed as a value between 0 and 1. Represents conversion losses, internal resistance, and inverter losses. Unit: fraction."""
    self_discharge_rate: float | None
    """Fraction of stored energy lost per time step due to self-discharge. Unit: fraction."""
    minimum_state_of_charge: float | None
    """Minimum allowed state of charge, usually expressed as a fraction between 0 and 1 Unit: fraction."""
    maximum_state_of_charge: float | None
    """Maximum allowed state of charge, usually expressed as a fraction between 0 and 1. Unit: fraction."""
    maximum_required_units: int | None
    """Maximum number of discrete technology units that may be installed, representing site or policy constraints on deployment. Unit: unit."""
    minimum_required_units: int | None
    """Minimum number of discrete technology units that must be installed, representing modular build constraints or policy minimums. Unit: unit."""
    unit_nominal_size: float | None
    """Nominal capacity of a single technology unit (MW or MWh depending on type). Combined with minimum/maximum required units to define total installable capacity range. Unit: MW, MWh."""
    economic_lifetime: float | None
    """Economic/depreciation lifetime of the asset in years. Unit: years."""
    storage_technology_type: str | None
    """Storage technology category when no StorageType library entity is referenced."""
    @property
    def hasCarrier(self) -> CarrierProxy | None: ...
    @hasCarrier.setter
    def hasCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def storesResource(self) -> NaturalResourceProxy | None: ...
    @storesResource.setter
    def storesResource(self, value: NaturalResourceProxy | NaturalResourceId) -> None: ...

class StorageUnitProxy(EntityProxy):
    capacity_expansion: StorageUnitCapacityExpansionProxy
    dispatch: StorageUnitDispatchProxy
    topology: StorageUnitTopologyProxy
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    commissioning_year: int | None
    """Year in which the generation unit was first commissioned and became commercially operational. Instance-specific: determines actual age, real efficiency relative to nameplate, and remaining technical lifetime. Year alone is sufficient for planning and ageing models."""
    retrofit_date: datetime | None
    """Date of major upgrade or efficiency retrofit. Impacts operational efficiency, lifetime extension, and emission calculations. Unit: date."""
    retirement_date: datetime | None
    """Planned or actual date when the generator is permanently retired from service. Used for asset replacement planning and system expansion studies. Unit: date."""
    nominal_power_capacity: float | None
    """Maximum instantaneous power the asset, technology template, or conversion port can deliver or absorb, in MW. Defines operational limits for dispatch. Unit: MW."""
    energy_storage_capacity: float | None
    """Maximum net energy or storage medium volume that can be stored and subsequently released under defined operating conditions, expressed as the difference between maximum and minimum allowable state of charge. Use MWh for energy-equivalent storage models and m3 for reservoir water-volume models. Unit: MWh, m3."""
    annual_natural_inflow_energy: float | None
    """Total natural inflow received by a storage asset over one year. Used as the scaling factor when converting a normalised inflow profile (as_normalized_annual_energy) to absolute hourly inflow values in dispatch optimisation models. Unit: MWh/year."""
    charging_efficiency: float | None
    """The fraction of input energy that is successfully stored during the charging process, expressed as a value between 0 and 1. Accounts for losses in power electronics, conversion stages, and internal storage mechanisms. Unit: fraction."""
    discharging_efficiency: float | None
    """The fraction of stored energy that can be delivered as useful output during the discharging process, expressed as a value between 0 and 1. Represents conversion losses, internal resistance, and inverter losses. Unit: fraction."""
    self_discharge_rate: float | None
    """Fraction of stored energy lost per time step due to self-discharge. Unit: fraction."""
    minimum_state_of_charge: float | None
    """Minimum allowed state of charge, usually expressed as a fraction between 0 and 1 Unit: fraction."""
    maximum_state_of_charge: float | None
    """Maximum allowed state of charge, usually expressed as a fraction between 0 and 1. Unit: fraction."""
    initial_state_of_charge: float | None
    """Initial state of charge at the beginning of the optimization horizon, expressed as a fraction between 0 and 1. Unit: fraction."""
    maximum_ramp_rate_up: float | None
    """The maximum increase in output power per unit time, typically expressed in kW/s or MW/min. Represents the upward operational flexibility of the asset (a generator ramping up, or a storage device discharging faster). Unit: %/h."""
    maximum_ramp_rate_down: float | None
    """The maximum percentage decrease in output power per unit time during ramp-down operations. Expressed as %/min or %/s, capturing the asset's downward operational flexibility (a generator ramping down, or a storage device changing its charging/discharging rate). Unit: %/h."""
    variable_operating_cost: float | None
    """Marginal operating cost per unit of output (or throughput) used in dispatch optimisation. Unit: MU/MWh."""
    charging_variable_operating_cost: float | None
    """Marginal cost incurred per MWh of energy absorbed during the charging process, expressed in MU/MWh. Unit: MU/MWh."""
    maximum_charging_power: float | None
    """Upper limit on instantaneous power intake during charging, constrained by converter size and thermal limits (MW). Unit: MW."""
    maximum_discharging_power: float | None
    """Upper limit on instantaneous power output during discharging or generation, constrained by turbine/converter size and operating limits (MW). Unit: MW."""
    storage_technology_type: str | None
    """Storage technology category when no StorageType library entity is referenced."""
    @property
    def hasTechnology(self) -> StorageTypeProxy | None: ...
    @hasTechnology.setter
    def hasTechnology(self, value: StorageTypeProxy | StorageTypeId) -> None: ...
    @property
    def storesCarrier(self) -> CarrierProxy | None: ...
    @storesCarrier.setter
    def storesCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def storesResource(self) -> NaturalResourceProxy | None: ...
    @storesResource.setter
    def storesResource(self, value: NaturalResourceProxy | NaturalResourceId) -> None: ...
    @property
    def hasNaturalInflowProfile(self) -> ProfileProxy | None: ...
    @hasNaturalInflowProfile.setter
    def hasNaturalInflowProfile(self, value: ProfileProxy | str) -> None: ...
    @property
    def atNode(self) -> NetworkNodeProxy | None: ...
    @atNode.setter
    def atNode(self, value: NetworkNodeProxy | str) -> None: ...
    @property
    def belongsToGeographicalRegion(self) -> GeographicalRegionProxy | None: ...
    @belongsToGeographicalRegion.setter
    def belongsToGeographicalRegion(self, value: GeographicalRegionProxy | str) -> None: ...

class SystemAssetProxy(EntityProxy):
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""

class ThermalGenerationUnitProxy(EntityProxy):
    capacity_expansion: ThermalGenerationUnitCapacityExpansionProxy
    dispatch: ThermalGenerationUnitDispatchProxy
    dynamics: ThermalGenerationUnitDynamicsProxy
    technical: ThermalGenerationUnitTechnicalProxy
    topology: ThermalGenerationUnitTopologyProxy
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    commissioning_year: int | None
    """Year in which the generation unit was first commissioned and became commercially operational. Instance-specific: determines actual age, real efficiency relative to nameplate, and remaining technical lifetime. Year alone is sufficient for planning and ageing models."""
    retrofit_date: datetime | None
    """Date of major upgrade or efficiency retrofit. Impacts operational efficiency, lifetime extension, and emission calculations. Unit: date."""
    retirement_date: datetime | None
    """Planned or actual date when the generator is permanently retired from service. Used for asset replacement planning and system expansion studies. Unit: date."""
    rated_voltage: float | None
    """Rated line-to-line terminal voltage of the deployed generation unit [kV]. Together with rated_apparent_power, defines the machine-specific impedance base. Unit: kV."""
    rated_apparent_power: float | None
    """Rated apparent power of the deployed generation unit [MVA]. Defines the machine-specific per-unit power base used with a linked DynamicMachineModelType. Unit: MVA."""
    generator_technology_type: str | None
    """Generation technology category when no GeneratorType library entity is referenced."""
    nominal_power_capacity: float | None
    """Maximum instantaneous power the asset, technology template, or conversion port can deliver or absorb, in MW. Defines operational limits for dispatch. Unit: MW."""
    minimum_generation: float | None
    """The minimum active power output that the generation entity can continuously produce while remaining in stable operation. This value represents the lower operational dispatch limit of the generator and is typically expressed in MW. Unit: MW."""
    maximum_generation: float | None
    """The maximum active power output that the generation entity can produce under normal operating conditions. This value represents the upper operational dispatch limit of the generator and is typically expressed in MW. Unit: MW."""
    variable_operating_cost: float | None
    """Marginal operating cost per unit of output (or throughput) used in dispatch optimisation. Unit: MU/MWh."""
    fixed_operating_cost: float | None
    """Fixed operation and maintenance (O&M) cost associated with the technology, typically expressed per year and per unit of installed capacity or per unit of technology. Covers costs that do not depend on energy production. Unit: MU/year, MU/(kW/year), MU/(MW/year), MU/unit."""
    energy_conversion_efficiency: float | None
    """Ratio of useful output energy to input energy, expressed as a fraction (0–1). Determines efficiency of energy conversion processes. Unit: fraction."""
    annual_resource_potential: float | None
    """Specifies the total annually available quantity of a resource or carrier that can be utilized, harvested, extracted, or converted by the represented entity under the assumptions of the associated scenario or resource representation. Unit: MWh/year."""
    dispatch_type: str | None
    """Dispatch classification of a generation technology: "dispatchable" — operator can choose output (thermal, hydro reservoir) "nondispatchable" — output bounded by external resource (wind, solar, RoR) "must_run" — must generate at minimum level (nuclear baseload, CHP)"""
    maximum_ramp_rate_up: float | None
    """The maximum increase in output power per unit time, typically expressed in kW/s or MW/min. Represents the upward operational flexibility of the asset (a generator ramping up, or a storage device discharging faster). Unit: %/h."""
    maximum_ramp_rate_down: float | None
    """The maximum percentage decrease in output power per unit time during ramp-down operations. Expressed as %/min or %/s, capturing the asset's downward operational flexibility (a generator ramping down, or a storage device changing its charging/discharging rate). Unit: %/h."""
    cooling_type: str | None
    """Cooling system type for a thermal plant (once-through, tower, air, …)."""
    reactor_type: str | None
    """Nuclear reactor technology type. Determines neutron spectrum, coolant, moderator, fuel cycle, and safety characteristics. PWR: pressurised water reactor (most common globally). BWR: boiling water reactor. PHWR: pressurised heavy-water reactor (e.g. CANDU). SMR: small modular reactor (<300 MWe). Allowed values: PWR, BWR, PHWR, SMR."""
    reactor_thermal_power: float | None
    """Gross thermal power of the reactor core under rated conditions, in MW_th. Electrical output is this value times the net electrical efficiency. Useful heat from a conversion unit is nominal_thermal_power_capacity, not this field. Unit: MW_th."""
    minimum_up_time: float | None
    """Minimum number of hours a unit must remain online once started. Used in unit commitment models. Unit: h."""
    minimum_down_time: float | None
    """Minimum number of hours a unit must remain offline after shutdown. Used in unit commitment models. Unit: h."""
    hot_start_cost: float | None
    """Cost incurred to restart a generator that has been recently offline (hot state), expressed in monitary units. Reflects fuel and operational overhead. Unit: MU."""
    cold_start_cost: float | None
    """Cost incurred to restart a generator that has been offline for a long period (cold state), expressed in MU. Usually higher than hot start due to additional operational procedures. Unit: MU."""
    @property
    def hasTechnology(self) -> GeneratorTypeProxy | None: ...
    @hasTechnology.setter
    def hasTechnology(self, value: GeneratorTypeProxy | GeneratorTypeId) -> None: ...
    @property
    def hasInputResource(self) -> NaturalResourceProxy | None: ...
    @hasInputResource.setter
    def hasInputResource(self, value: NaturalResourceProxy | NaturalResourceId) -> None: ...
    @property
    def hasInputCarrier(self) -> CarrierProxy | None: ...
    @hasInputCarrier.setter
    def hasInputCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def hasOutputCarrier(self) -> CarrierProxy | None: ...
    @hasOutputCarrier.setter
    def hasOutputCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def hasAvailabilityProfile(self) -> ProfileProxy | None: ...
    @hasAvailabilityProfile.setter
    def hasAvailabilityProfile(self, value: ProfileProxy | str) -> None: ...
    @property
    def atNode(self) -> NetworkNodeProxy | None: ...
    @atNode.setter
    def atNode(self, value: NetworkNodeProxy | str) -> None: ...
    @property
    def belongsToGeographicalRegion(self) -> GeographicalRegionProxy | None: ...
    @belongsToGeographicalRegion.setter
    def belongsToGeographicalRegion(self, value: GeographicalRegionProxy | str) -> None: ...

class TimestampSeriesProxy(EntityProxy):
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    start_datetime: str
    """ISO 8601 datetime string marking the first timestep of the series (e.g. "2009-01-01T00:00:00"). Combined with resolution and length this fully defines the time axis without storing the full array."""
    resolution: str
    """ISO 8601 duration string defining the uniform step size between consecutive timesteps (e.g. "PT1H" for hourly, "PT15M" for quarter-hourly, "P1D" for daily). All timesteps within one TimestampSeries are assumed to have equal duration."""
    length: int
    """Total number of timesteps in the series. Must equal the length of the values array stored in the HDF5 file for every Profile that references this TimestampSeries."""
    timezone: str | None
    """IANA timezone identifier for the series (e.g. "UTC", "Europe/Zurich"). Used when converting between local time and epoch timestamps. Defaults to UTC if not specified."""

class TransformerProxy(EntityProxy):
    capacity_expansion: TransformerCapacityExpansionProxy
    dispatch: TransformerDispatchProxy
    power_flow: TransformerPowerFlowProxy
    topology: TransformerTopologyProxy
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    commissioning_year: int | None
    """Year in which the generation unit was first commissioned and became commercially operational. Instance-specific: determines actual age, real efficiency relative to nameplate, and remaining technical lifetime. Year alone is sufficient for planning and ageing models."""
    retrofit_date: datetime | None
    """Date of major upgrade or efficiency retrofit. Impacts operational efficiency, lifetime extension, and emission calculations. Unit: date."""
    retirement_date: datetime | None
    """Planned or actual date when the generator is permanently retired from service. Used for asset replacement planning and system expansion studies. Unit: date."""
    from_switch_closed: bool | None
    """Boolean indicating whether the breaker at the from-end of the branch is closed (true = connected, false = disconnected). Used in contingency and outage modelling."""
    to_switch_closed: bool | None
    """Boolean indicating whether the breaker at the to-end of the branch is closed (true = connected, false = disconnected). Used in contingency and outage modelling."""
    thermal_capacity_rating: float | None
    """Maximum continuous apparent power the branch can carry without exceeding thermal limits, expressed in MVA. Unit: MVA."""
    @property
    def fromNode(self) -> ElectricalBusProxy | None: ...
    @fromNode.setter
    def fromNode(self, value: ElectricalBusProxy | str) -> None: ...
    @property
    def toNode(self) -> ElectricalBusProxy | None: ...
    @toNode.setter
    def toNode(self, value: ElectricalBusProxy | str) -> None: ...

class TransmissionElementProxy(EntityProxy):
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    commissioning_year: int | None
    """Year in which the generation unit was first commissioned and became commercially operational. Instance-specific: determines actual age, real efficiency relative to nameplate, and remaining technical lifetime. Year alone is sufficient for planning and ageing models."""
    retrofit_date: datetime | None
    """Date of major upgrade or efficiency retrofit. Impacts operational efficiency, lifetime extension, and emission calculations. Unit: date."""
    retirement_date: datetime | None
    """Planned or actual date when the generator is permanently retired from service. Used for asset replacement planning and system expansion studies. Unit: date."""
    from_switch_closed: bool | None
    """Boolean indicating whether the breaker at the from-end of the branch is closed (true = connected, false = disconnected). Used in contingency and outage modelling."""
    to_switch_closed: bool | None
    """Boolean indicating whether the breaker at the to-end of the branch is closed (true = connected, false = disconnected). Used in contingency and outage modelling."""
    @property
    def fromNode(self) -> NetworkNodeProxy | None: ...
    @fromNode.setter
    def fromNode(self, value: NetworkNodeProxy | str) -> None: ...
    @property
    def toNode(self) -> NetworkNodeProxy | None: ...
    @toNode.setter
    def toNode(self, value: NetworkNodeProxy | str) -> None: ...

class TransmissionLineProxy(EntityProxy):
    capacity_expansion: TransmissionLineCapacityExpansionProxy
    dispatch: TransmissionLineDispatchProxy
    power_flow: TransmissionLinePowerFlowProxy
    topology: TransmissionLineTopologyProxy
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    commissioning_year: int | None
    """Year in which the generation unit was first commissioned and became commercially operational. Instance-specific: determines actual age, real efficiency relative to nameplate, and remaining technical lifetime. Year alone is sufficient for planning and ageing models."""
    retrofit_date: datetime | None
    """Date of major upgrade or efficiency retrofit. Impacts operational efficiency, lifetime extension, and emission calculations. Unit: date."""
    retirement_date: datetime | None
    """Planned or actual date when the generator is permanently retired from service. Used for asset replacement planning and system expansion studies. Unit: date."""
    from_switch_closed: bool | None
    """Boolean indicating whether the breaker at the from-end of the branch is closed (true = connected, false = disconnected). Used in contingency and outage modelling."""
    to_switch_closed: bool | None
    """Boolean indicating whether the breaker at the to-end of the branch is closed (true = connected, false = disconnected). Used in contingency and outage modelling."""
    thermal_capacity_rating: float | None
    """Maximum continuous apparent power the branch can carry without exceeding thermal limits, expressed in MVA. Unit: MVA."""
    @property
    def fromNode(self) -> ElectricalBusProxy | None: ...
    @fromNode.setter
    def fromNode(self, value: ElectricalBusProxy | str) -> None: ...
    @property
    def toNode(self) -> ElectricalBusProxy | None: ...
    @toNode.setter
    def toNode(self, value: ElectricalBusProxy | str) -> None: ...

class WindGenerationUnitProxy(EntityProxy):
    capacity_expansion: WindGenerationUnitCapacityExpansionProxy
    dispatch: WindGenerationUnitDispatchProxy
    dynamics: WindGenerationUnitDynamicsProxy
    technical: WindGenerationUnitTechnicalProxy
    topology: WindGenerationUnitTopologyProxy
    name: str | None
    """Descriptive name."""
    long_name: str | None
    """Long description"""
    description: str | None
    """Textual description providing additional semantic, contextual, or explanatory information about the entity."""
    commissioning_year: int | None
    """Year in which the generation unit was first commissioned and became commercially operational. Instance-specific: determines actual age, real efficiency relative to nameplate, and remaining technical lifetime. Year alone is sufficient for planning and ageing models."""
    retrofit_date: datetime | None
    """Date of major upgrade or efficiency retrofit. Impacts operational efficiency, lifetime extension, and emission calculations. Unit: date."""
    retirement_date: datetime | None
    """Planned or actual date when the generator is permanently retired from service. Used for asset replacement planning and system expansion studies. Unit: date."""
    rated_voltage: float | None
    """Rated line-to-line terminal voltage of the deployed generation unit [kV]. Together with rated_apparent_power, defines the machine-specific impedance base. Unit: kV."""
    rated_apparent_power: float | None
    """Rated apparent power of the deployed generation unit [MVA]. Defines the machine-specific per-unit power base used with a linked DynamicMachineModelType. Unit: MVA."""
    generator_technology_type: str | None
    """Generation technology category when no GeneratorType library entity is referenced."""
    nominal_power_capacity: float | None
    """Maximum instantaneous power the asset, technology template, or conversion port can deliver or absorb, in MW. Defines operational limits for dispatch. Unit: MW."""
    minimum_generation: float | None
    """The minimum active power output that the generation entity can continuously produce while remaining in stable operation. This value represents the lower operational dispatch limit of the generator and is typically expressed in MW. Unit: MW."""
    maximum_generation: float | None
    """The maximum active power output that the generation entity can produce under normal operating conditions. This value represents the upper operational dispatch limit of the generator and is typically expressed in MW. Unit: MW."""
    variable_operating_cost: float | None
    """Marginal operating cost per unit of output (or throughput) used in dispatch optimisation. Unit: MU/MWh."""
    fixed_operating_cost: float | None
    """Fixed operation and maintenance (O&M) cost associated with the technology, typically expressed per year and per unit of installed capacity or per unit of technology. Covers costs that do not depend on energy production. Unit: MU/year, MU/(kW/year), MU/(MW/year), MU/unit."""
    energy_conversion_efficiency: float | None
    """Ratio of useful output energy to input energy, expressed as a fraction (0–1). Determines efficiency of energy conversion processes. Unit: fraction."""
    annual_resource_potential: float | None
    """Specifies the total annually available quantity of a resource or carrier that can be utilized, harvested, extracted, or converted by the represented entity under the assumptions of the associated scenario or resource representation. Unit: MWh/year."""
    dispatch_type: str | None
    """Dispatch classification of a generation technology: "dispatchable" — operator can choose output (thermal, hydro reservoir) "nondispatchable" — output bounded by external resource (wind, solar, RoR) "must_run" — must generate at minimum level (nuclear baseload, CHP)"""
    maximum_ramp_rate_up: float | None
    """The maximum increase in output power per unit time, typically expressed in kW/s or MW/min. Represents the upward operational flexibility of the asset (a generator ramping up, or a storage device discharging faster). Unit: %/h."""
    maximum_ramp_rate_down: float | None
    """The maximum percentage decrease in output power per unit time during ramp-down operations. Expressed as %/min or %/s, capturing the asset's downward operational flexibility (a generator ramping down, or a storage device changing its charging/discharging rate). Unit: %/h."""
    hub_height: float | None
    """Height of the wind turbine hub above ground level. Determines the wind speed at rotor height via the wind shear profile, and therefore directly affects annual energy yield. Instance-specific: two turbines of the same type may have different hub heights depending on site conditions. Unit: m."""
    rotor_diameter: float | None
    """Diameter of the wind turbine rotor. Together with hub_height, determines the swept area and the rated power curve. Instance-specific. Unit: m."""
    installation_type: str | None
    """Installation category of the wind turbine. Determines foundation type, accessibility, and O&M cost profile. Allowed values: onshore, offshore, floating_offshore."""
    number_of_turbines: int | None
    """Number of individual wind turbines within this GenerationUnit (wind farm). Used to derive per-turbine statistics and wake-loss modelling."""
    @property
    def hasTechnology(self) -> GeneratorTypeProxy | None: ...
    @hasTechnology.setter
    def hasTechnology(self, value: GeneratorTypeProxy | GeneratorTypeId) -> None: ...
    @property
    def hasInputResource(self) -> NaturalResourceProxy | None: ...
    @hasInputResource.setter
    def hasInputResource(self, value: NaturalResourceProxy | NaturalResourceId) -> None: ...
    @property
    def hasInputCarrier(self) -> CarrierProxy | None: ...
    @hasInputCarrier.setter
    def hasInputCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def hasOutputCarrier(self) -> CarrierProxy | None: ...
    @hasOutputCarrier.setter
    def hasOutputCarrier(self, value: CarrierProxy | CarrierId) -> None: ...
    @property
    def hasAvailabilityProfile(self) -> ProfileProxy | None: ...
    @hasAvailabilityProfile.setter
    def hasAvailabilityProfile(self, value: ProfileProxy | str) -> None: ...
    @property
    def atNode(self) -> NetworkNodeProxy | None: ...
    @atNode.setter
    def atNode(self, value: NetworkNodeProxy | str) -> None: ...
    @property
    def belongsToGeographicalRegion(self) -> GeographicalRegionProxy | None: ...
    @belongsToGeographicalRegion.setter
    def belongsToGeographicalRegion(self, value: GeographicalRegionProxy | str) -> None: ...

class CesdmProxy(EntityProxy):
    pass

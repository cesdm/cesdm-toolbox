# Copyright (c) 2026 Research Center for Energy Networks - ETH Zürich
# The CESDM project is part of the SWEET-CoSi consortium, funded by the
# Swiss Federal Office of Energy (SFOE) through its SWEET programme.

"""AUTO-GENERATED CESDM proxy subclasses.

Do not edit manually. Run ``cesdm-generate-api`` after schema changes.
"""
from __future__ import annotations

from cesdm.proxy import EntityProxy

class SemanticEntityProxy(EntityProxy):
    """Proxy for CESDM entity class ``SemanticEntity``."""
    pass

class SystemAssetProxy(SemanticEntityProxy):
    """Proxy for CESDM entity class ``SystemAsset``."""
    pass

class EnergyAssetInstanceProxy(SystemAssetProxy):
    """Proxy for CESDM entity class ``EnergyAssetInstance``."""
    pass

class ConversionUnitProxy(EnergyAssetInstanceProxy):
    """Proxy for CESDM entity class ``ConversionUnit``."""
    pass

class BoilerUnitProxy(ConversionUnitProxy):
    """Proxy for CESDM entity class ``BoilerUnit``."""
    pass

class CHPUnitProxy(ConversionUnitProxy):
    """Proxy for CESDM entity class ``CHPUnit``."""
    pass

class CarrierProxy(SemanticEntityProxy):
    """Proxy for CESDM entity class ``Carrier``."""
    pass

class CarrierDomainProxy(SemanticEntityProxy):
    """Proxy for CESDM entity class ``CarrierDomain``."""
    pass

class PortProxy(SemanticEntityProxy):
    """Proxy for CESDM entity class ``Port``."""
    pass

class ConversionPortProxy(PortProxy):
    """Proxy for CESDM entity class ``ConversionPort``."""
    pass

class DemandUnitProxy(EnergyAssetInstanceProxy):
    """Proxy for CESDM entity class ``DemandUnit``."""
    pass

class NetworkNodeProxy(SemanticEntityProxy):
    """Proxy for CESDM entity class ``NetworkNode``."""
    pass

class ElectricalBusProxy(NetworkNodeProxy):
    """Proxy for CESDM entity class ``ElectricalBus``."""
    pass

class TransmissionElementProxy(EnergyAssetInstanceProxy):
    """Proxy for CESDM entity class ``TransmissionElement``."""
    pass

class ElectricityTransmissionProxy(TransmissionElementProxy):
    """Proxy for CESDM entity class ``ElectricityTransmission``."""
    pass

class ElectrolyserUnitProxy(ConversionUnitProxy):
    """Proxy for CESDM entity class ``ElectrolyserUnit``."""
    pass

class EnergySystemModelProxy(SemanticEntityProxy):
    """Proxy for CESDM entity class ``EnergySystemModel``."""
    pass

class EnergyTechnologyTypeProxy(SemanticEntityProxy):
    """Proxy for CESDM entity class ``EnergyTechnologyType``."""
    pass

class ExternalSupplyProxy(EnergyAssetInstanceProxy):
    """Proxy for CESDM entity class ``ExternalSupply``."""
    pass

class FuelCellUnitProxy(ConversionUnitProxy):
    """Proxy for CESDM entity class ``FuelCellUnit``."""
    pass

class GasBusProxy(NetworkNodeProxy):
    """Proxy for CESDM entity class ``GasBus``."""
    pass

class GenerationUnitProxy(EnergyAssetInstanceProxy):
    """Proxy for CESDM entity class ``GenerationUnit``."""
    pass

class GeneratorTypeProxy(EnergyTechnologyTypeProxy):
    """Proxy for CESDM entity class ``GeneratorType``."""
    pass

class GenericConversionUnitProxy(ConversionUnitProxy):
    """Proxy for CESDM entity class ``GenericConversionUnit``."""
    pass

class GenericInterconnectorProxy(TransmissionElementProxy):
    """Proxy for CESDM entity class ``GenericInterconnector``."""
    pass

class GeographicalRegionProxy(SemanticEntityProxy):
    """Proxy for CESDM entity class ``GeographicalRegion``."""
    pass

class HVDCLinkProxy(ElectricityTransmissionProxy):
    """Proxy for CESDM entity class ``HVDCLink``."""
    pass

class HeatBusProxy(NetworkNodeProxy):
    """Proxy for CESDM entity class ``HeatBus``."""
    pass

class HeatPumpUnitProxy(ConversionUnitProxy):
    """Proxy for CESDM entity class ``HeatPumpUnit``."""
    pass

class HydroGenerationUnitProxy(GenerationUnitProxy):
    """Proxy for CESDM entity class ``HydroGenerationUnit``."""
    pass

class HydroReservoirProxy(EnergyAssetInstanceProxy):
    """Proxy for CESDM entity class ``HydroReservoir``."""
    pass

class HydrogenBusProxy(NetworkNodeProxy):
    """Proxy for CESDM entity class ``HydrogenBus``."""
    pass

class NaturalResourceProxy(SemanticEntityProxy):
    """Proxy for CESDM entity class ``NaturalResource``."""
    pass

class ProfileProxy(SemanticEntityProxy):
    """Proxy for CESDM entity class ``Profile``."""
    pass

class SolarGenerationUnitProxy(GenerationUnitProxy):
    """Proxy for CESDM entity class ``SolarGenerationUnit``."""
    pass

class StorageTypeProxy(EnergyTechnologyTypeProxy):
    """Proxy for CESDM entity class ``StorageType``."""
    pass

class StorageUnitProxy(EnergyAssetInstanceProxy):
    """Proxy for CESDM entity class ``StorageUnit``."""
    pass

class ThermalGenerationUnitProxy(GenerationUnitProxy):
    """Proxy for CESDM entity class ``ThermalGenerationUnit``."""
    pass

class TimestampSeriesProxy(SemanticEntityProxy):
    """Proxy for CESDM entity class ``TimestampSeries``."""
    pass

class TransformerProxy(ElectricityTransmissionProxy):
    """Proxy for CESDM entity class ``Transformer``."""
    pass

class TransmissionLineProxy(ElectricityTransmissionProxy):
    """Proxy for CESDM entity class ``TransmissionLine``."""
    pass

class WindGenerationUnitProxy(GenerationUnitProxy):
    """Proxy for CESDM entity class ``WindGenerationUnit``."""
    pass

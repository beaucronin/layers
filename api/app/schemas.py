import json
from typing import Optional, Literal
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Extra


# Observations

# https://github.com/google/open-location-code/wiki/Evaluation-of-Location-Encoding-Systems

class LatLongLocation(BaseModel):
    """A location, specified by a longitude and latitude as floats"""
    longitude: str
    latitude: str


class GeohashLocation(BaseModel):
    """A location, specified as a geohash"""
    geohash: str

    class Config:
        json_loads = json.loads
        json_dumps = json.dumps


class PlusCodeLocation(BaseModel):
    """A location, specified as a plus code"""
    pluscode: str


class AddressLocation(BaseModel):
    """A location, specified by an address"""
    address: str


Location = LatLongLocation | GeohashLocation | PlusCodeLocation


class PayloadRef(BaseModel):
    ref: str | int


class Observation(BaseModel, extra=Extra.forbid):
    """The abstract base model for an observation, which may optionally contain a payload reference"""

    payload_ref: Optional[str | int]


class AssetObservation(Observation):
    """An observation of an asset"""

    class VehicleType(str, Enum):
        """The enum of valid vehicle types for AssetObservations"""
        CONTAINER_SHIP = "vehicle:ship:container"
        OIL_TANKER = "vehicle:ship:oil"
        BULK_CARRIER = "vehicle:ship:bulk"
        RAIL_CAR = "vehicle:rail:car"
        SEMI_TRACTOR = "vehicle:truck:semi_tractor"
        PANEL_TRUCK = "vehicle:truck:panel"
        DELIVERY_VAN = "vehicle:truck:delivery_van"
        CARGO_AIRCRAFT = "vehicle:aircraft:cargo"
        PASSENGER_AIRCRAFT = "vehicle:aircraft:passenger"

    class ContainerType(str, Enum):
        """The enum of valid container types for AssetObservations"""
        SHIPPING_CONTAINER_40 = "container:multimodal_container:40ft"
        SHIPPING_CONTAINER_20 = "container:multimodal_container:20ft"
        SHIPPING_CONTAINER_10 = "container:multimodal_container:10ft"
        TRACTOR_TRAILER = "container:trailer:enclosed"
        REFRIGERATED_TRAILER = "container:trailer:refrigerated"
        LIVESTOCK_TRAILER = "container:trailer:livestock"
        TANK_TRAILER = "container:trailer:tank"
        METAL_TANK = "container:tank:metal"
        PLASTIC_TANK = "container:tank:plastic"

    class AssetId(BaseModel):
        """A fragment describing an Asset ID"""

        class IDType(str, Enum):
            US_LICENSE = "plate:united_states"
            BIC = "BIC"

        id_type: IDType
        id_text: str

    class AssetConfiguration(str, Enum):
        FREE_STANDING = "open:free_standing"
        STACKED = "open:stacked"
        PAD_MOUNTED = "mounted:pad"
        TRAILER_MOUNTED = "mounted:trailer"
        POLE_MOUNTED = "mounted:pole"
        TOWER_MOUNTED = "mounted:tower"
        SHELF_MOUNTED = "mounted:shelf"
        STATIONARY_ROAD = "stationary:road"
        STATIONARY_RAIL = "stationary:rail"
        STATIONARY = "stationary:other"
        MOVING_ROAD = "moving:road"
        MOVING_RAIL = "moving:rail"
        MOVING_MARINE = "moving:marine"
        MOVING_AIRBORNE = "moving:airborne"

    observation_type: Literal['asset']
    asset_type: VehicleType | ContainerType | Literal["asset:generic"]
    asset_id: AssetId | list[AssetId]
    configuration: Optional[AssetConfiguration]


class TransportObservation(Observation):
    """An observation of a transportation, optionally referring to other observation payloads"""

    class TransportMode(str, Enum):
        """The basic modes of transport that a TransportObservation can describe"""
        RAIL = "rail"
        SEMI_TRAILER = "semi_trailer"
        SHIP = "ship"
        TRUCK = "truck"
        PIPELINE = "pipeline"

    class Route(BaseModel):
        pass
        # description = Optional[str]
        # waypoints = list[Location]

    observation_type: Literal['transport']
    mode: TransportMode
    transporter: Optional[PayloadRef | list[PayloadRef]]
    vessel: Optional[PayloadRef | list[PayloadRef]]
    route: Optional[Route]


class FacilityObservation(Observation):
    """An observation of a facility"""

    FD_DATA = [
        ["energy", "electricity:voltage:lower", "Electricity ➤ Lower Voltage", "#4455ee"],        
        ["energy", "electricity:voltage:raise", "Electricity ➤ Raise Voltage", "#4455ee"],        
        ["energy", "electricity:generate", "Electricity ➤ Generate", "#4455ee"],        
        ["energy", "electricity:store", "Electricity ➤ Store", "#4455ee"],        
        ["energy", "electricity:condition", "Electricity ➤ Condition", "#4455ee"],
        ["factory", "textile", "Factory ➤ Textile", "#ee5544"],
        ["factory", "equipment", "Factory ➤ Equipment", "#ee5544"],
        ["factory", "food", "Factory ➤ Food", "#ee5544"],
        ["factory", "material", "Factory ➤ Material", "#ee5544"],
        ["mine", "gold", "Mine ➤ Gold", "#eeaa44"],
        ["mine", "silver", "Mine ➤ Silver", "#eeaa44"],
        ["mine", "platinum", "Mine ➤ Platinum", "#eeaa44"],
        ["mine", "limestone", "Mine ➤ Limestone", "#eeaa44"],
        ["mine", "coal", "Mine ➤ Coal", "#eeaa44"],
        ["mine", "gravel", "Mine ➤ Gravel", "#eeaa44"],
        ["mine", "sand", "Mine ➤ Sand", "#eeaa44"],
        ["mine", "bauxite", "Mine ➤ Bauxite", "#eeaa44"],
        ["mine", "lithium", "Mine ➤ Lithium", "#eeaa44"],
        ["mine", "uranium", "Mine ➤ Uranium", "#eeaa44"],
        ["mine", "potash", "Mine ➤ Potash", "#eeaa44"],
        ["mine", "sulfur", "Mine ➤ Sulfur", "#eeaa44"],
        ["mine", "salt", "Mine ➤ Salt", "#eeaa44"],
        ["mine", "iron", "Mine ➤ Iron", "#eeaa44"],
        ["mine", "coltan", "Mine ➤ Coltan", "#eeaa44"],
        ["refinery", "oil", "Refinery ➤ Oil", "#9999aa"],
        ["refinery", "metal", "Refinery ➤ Metal", "#9999aa"],
        ["refinery", "other", "Refinery ➤ Other", "#9999aa"],
    ]

    class FacilityDescription(BaseModel):
        class EnergyType(str, Enum):
            LOWER_VOLTAGE = "electricity:voltage:lower"
            RAISE_VOLTAGE = "electricity:voltage:raise"
            GENERATE_ELECTRICITY = "electricity:generate"
            STORE_ELECTRICITY = "electricity:store"
            CONDITION_ELECTRICITY = "electricity:condition"

        class FactoryType(str, Enum):
            TEXTILE = "textile"
            EQUIPMENT = "equipment"
            FOOD = "food"
            MATERIAL = "material"

        class MineType(str, Enum):
            GOLD = "gold"
            SILVER = "silver"
            PLATINUM = "platinum"
            LIMESTONE = "limestone"
            COAL = "coal"
            GRAVEL = "gravel"
            SAND = "sand"
            BAUXITE = "bauxite"
            LITHIUM = "lithium"
            URANIUM = "uranium"
            POTASH = "potash"
            SULFUR = "sulfur"
            SALT = "salt"
            RARE_EARTH = "rare_earth"
            IRON = "iron"
            COLTAN = "coltan"

        class RefineryType(str, Enum):
            PETROLEUM = "petroleum"
            METAL = "metal"
            OTHER = "other"

        energy: Optional[EnergyType | list[EnergyType]]
        factory: Optional[FactoryType | list[FactoryType]]
        mine: Optional[MineType | list[MineType]]
        refinery: Optional[RefineryType | list[RefineryType]]

    PROCESS_DATA = [
        ["Extraction", "Surface Mining", "Open Pit"],
        ["Extraction", "Surface Mining", "Strip"],
        ["Extraction", "Underground Mining", "Shaft"],
        ["Extraction", "Underground Mining", "Drift"],
        ["Extraction", "Underground Mining", "Slope"],
        ["Reaction", "Chloralkali"],
        ["Reaction", "Calcination"],
        ["Reaction", "Smelting"],
        ["Reaction", "Bayer"],
        ["Reaction", "Hall-Heroult"],
        ["Reaction", "Distillation"],
        ["Reaction", "Brewing"],
        ["Reaction", "Electroplating"],
        ["Reaction", "Electrowinning"],
        ["Reaction", "Electropolishing"],
        ["Reaction", "Anodizing"],
        ["Reaction", "Electrolysis"],

    ]

    class Process(str, Enum):
        OPEN_PIT_MINING = "extraction:surface_mining:open_pit"
        STRIP_MINING = "extraction:surface_mining:strip"
        SHAFT_MINING = "extraction:underground_mining:shaft"
        DRIFT_MINING = "extraction:underground_mining:drift"
        SLOPE_MINING = "extraction:underground_mining:slope"

        CHLORALKALI = "reaction:chloralkali"
        CALCINATION = "reaction:calcination"
        SMELTING = "reaction:smelting"
        BAYER = "reaction:bayer"
        HALL_HEROULT = "reaction:hall_heroult"

        DISTILLATION = "reaction:distillation"
        BREWING = "reaction:brewing"

        ELECTROPLATING = "reaction:electroplating"
        ELECTROWINNING = "reaction:electrowinning"
        ELECTROPOLISHING = "reaction:electropolishing"
        ANODIZING = "reaction:anodizing"
        ELECTROLYSIS = "reaction:electrolysis"

        MACHINING = "fabrication:machining"
        CNC = "fabrication:machining:cnc"
        CUTTING = "fabrication:machining:cutting"
        FDM = "fabrication:additive:fdm"
        SLS = "fabrication:additive:sls"
        SLA = "fabrication:additive:sla"
        WELDING = "fabrication:welding"
        PAINTING = "fabrication:painting"
        ASSEMBLY = "fabrication:assembly"
        CASTING = "fabrication:casting"
        FORGING = "fabrication:forging"
        INJECTION_MOLDING = "fabrication:injection_molding"
        FABRICATION = "fabrication:various"

        GINNING = "textile:ginning"
        CARDING = "textile:carding"
        COMBING = "textile:combing"
        SPINNING = "textile:spinning"
        WINDING = "textile:winding"
        WARPING = "textile:warping"
        WEAVING = "textile:weaving"

        WASTEWATER_TREATMENT = "water:treatment"
        DESALINATION = "water:desalination"

    observation_type: Literal['facility']
    description: str
    facility_description: FacilityDescription
    processes: Optional[Process | list[Process]]

class Shape(BaseModel):
    pass

class ResourceObservation(Observation):
    """An observation of a natural resource"""

    class ResourceId(BaseModel):
        """A fragment describing a Resource ID"""

        class IDType(str, Enum):
            pass

        id_type: IDType
        id_text: str

    class Amount(BaseModel):
        """An amount of a resource"""

        class ResourceUnit(str, Enum):
            ACRE = "acre"
            HECTARE = "hectare"
            SQUARE_METER = "m2"
            ACRE_FOOT = "acre_foot"
            GALLON = "gallon"
            CUBIC_METER = "m3"
            TON = "ton"  # short ton; 2000 pounds
            TONNE = "tonne"  # metric ton; 1000 kg
            BARREL = "bbl"
            POUNDS = "lbs"
            KILOGRAMS = "kg"
            BTU = "btu"

        unit: ResourceUnit
        quantity: str | float

    observation_type: Literal['resource']
    description: str
    resource_id: ResourceId
    amount: Amount
    shape: Optional[Shape]


class ExtentObservation(Observation):
    """An observation of a human-defined bounary or area"""

    shape: Optional[Shape]


class SourceType(str, Enum):
    DIRECT = "direct"
    SCRAPE = "scrape"
    ONLINE = "online"
    CAPTURE = "capture"
    OTHER = "other"


SomeObservation = AssetObservation | TransportObservation | FacilityObservation


class ObservationWrapper(BaseModel, extra=Extra.forbid, title="Observation"):
    """NOTE: This schema is automatically generated and should not be modified here"""
    observer: str
    source: SourceType
    observed_at: datetime
    submitted_at: datetime
    location: Location
    # location: str
    payload: SomeObservation | list[SomeObservation]


def main():
    """Generates the json schemas and places them in the ./schemas/ folder"""

    with open(f"schemas/observation_schema.json", "w") as fd:
        fd.write(ObservationWrapper.schema_json(indent=2))


if __name__ == "__main__":
    main()

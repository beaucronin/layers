from typing import Optional, Literal
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Extra


# Observations

# https://github.com/google/open-location-code/wiki/Evaluation-of-Location-Encoding-Systems

class LatLongLocation(BaseModel):
    """A location, specified by a longitude and latitude as floats"""
    longitude: float
    latitude: float


class GeohashLocation(BaseModel):
    """A location, specified as a geohash"""
    geohash: str


class PlusCodeLocation(BaseModel):
    """A location, specified as a plus code"""
    pluscode: str


class PayloadRef(BaseModel):
    ref: str | int


class Observation(BaseModel, extra=Extra.forbid):
    """The abstract base model for an observation, which may optionally contain a payload reference"""

    payload_ref: Optional[str | int]


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
    METAL_TANK = "container:tank:metal"
    PLASTIC_TANK = "container:tank:plastic"


class AssetId(BaseModel):
    """A fragment describing an Asset ID"""

    class IDType(str, Enum):
        US_LICENSE = "plate:united_states"
        BIC = "BIC"

    id_type: IDType
    id_text: str


class AssetObservation(Observation):
    """An observation of an asset"""

    class AssetConfiguration(str, Enum):
        FREE_STANDING = "free_standing"
        STACKED = "stacked"
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


class TransportMode(str, Enum):
    """The basic modes of transport that a TransportObservation can describe"""
    RAIL = "rail"
    SEMI_TRAILER = "semi_trailer"
    SHIP = "ship"
    TRUCK = "truck"


class TransportObservation(Observation):
    """An observation of a transportation, optionally referring to other observation payloads"""
    observation_type: Literal['transport']
    mode: TransportMode
    transporter: Optional[PayloadRef]
    vessel: Optional[PayloadRef]


class Factory(BaseModel):
    pass


class FacilityDescription(BaseModel):
    class MineType(str, Enum):
        LIMESTONE = "limestone"
        GOLD = "gold"

    class FactoryType(str, Enum):
        TEXTILE = "textile"
        EQUIPMENT = "equipment"
        FOOD = "food"

    class RefineryType(str, Enum):
        PETROLEUM = "petroleum"
        METAL = "metal"
    
    class EnergyType(str, Enum):
        LOWER_VOLTAGE = "electricity:voltage:lower"
        RAISE_VOLTAGE = "electricity:voltage:raise"
        GENERATE_ELECTRICITY = "electricity:generate"
        VOLTAGE_REDUCE = "voltage"

    energy: Optional[EnergyType | list[EnergyType]]
    mine: Optional[MineType | list[MineType]]


class Process(str, Enum):
    SURFACE_MINING = "process:extraction:surface_mining"

    CHLORALKALI = "process:reaction:chloralkali"
    CALCINATION = "process:reaction:calcination"
    SMELTING = "process:reaction:smelting"
    BAYER = "process:reaction:bayer"
    HALL_HEROULT = "process:reaction:hall_heroult"


class FacilityObservation(Observation):
    """An observation of a facility"""
    observation_type: Literal['facility']
    description: str
    facility_description: FacilityDescription
    processes: Optional[Process | list[Process]]


class SourceType(str, Enum):
    DIRECT = "direct"
    SCRAPE = "scrape"
    ONLINE = "online"
    CAPTURE = "capture"
    OTHER = "other"


SomeObservation = AssetObservation | TransportObservation | FacilityObservation


class ObservationWrapper(BaseModel, extra=Extra.forbid):
    """The base schema for all observations"""
    observer: str
    source: SourceType
    observed_at: datetime
    submitted_at: datetime
    location: LatLongLocation | GeohashLocation | PlusCodeLocation
    payload: SomeObservation | list[SomeObservation]


def main():
    """Generates the json schemas and places them in the ./schemas/ folder"""

    with open(f"schemas/observation_schema.json", "w") as fd:
        fd.write(ObservationWrapper.schema_json(indent=2))


if __name__ == "__main__":
    main()

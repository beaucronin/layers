import json
from typing import Optional, Literal
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Extra
from geojson_pydantic import FeatureCollection, Feature, Point

# Observations

# https://github.com/google/open-location-code/wiki/Evaluation-of-Location-Encoding-Systems

class LatLongLocation(BaseModel):
    """A location, specified by a longitude and latitude as floats"""
    longitude: str | float
    latitude: str | float


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

    class FacilityFunction(str, Enum):
        LOWER_ELECTRICITY_VOLTAGE = "energy:electricity:voltage:lower"
        RAISE_ELECTRICITY_VOLTAGE = "energy:electricity:voltage:raise"
        GENERATE_ELECTRICITY = "energy:electricity:generate"
        STORE_ELECTRICITY = "energy:electricity:store"
        CONDITION_ELECTRICITY = "energy:electricity:condition"
        TRANSMIT_ELECTRICITY = "energy:electricity:transmit"

        TEXTILE = "factory:textile"
        EQUIPMENT = "factory:equipment"
        FOOD = "factory:food"
        CHEMICAL = "factory:chemical"
        MATERIAL = "factory:material"
        WOOD_MILL = "factory:material:wood_mill"
        PAPER_MILL = "factory:material:paper_mill"
        METAL_FABRICATION = "factory:material:metal_fabrication"
        PLASTIC_FABRICATION = "factory:material:plastic_fabrication"
        FURNITURE_FACTORY = "factory:furniture"
        FACTORY = "factory:unspecified"

        AUTO_REPAIR = "repair:automotive"
        TRUCK_REPAIR = "repair:truck"
        ELECTRONIC_REPAIR = "repair:electronic"
        EQUIPMENT_REPAIR = "repair:equipment"
        APPLIANCE_REPAIR = "repair:appliance"
        REPAIR = "repair:unspecified"

        RETAIL = "retail:unspecified"
        FOOD_RETAIL = "retail:food"
        AUTO_RETAIL = "retail:automotive"
        ELECTRONIC_RETAIL = "retail:electronic"
        EQUIPMENT_RETAIL = "retail:equipment"
        APPLIANCE_RETAIL = "retail:appliance"
        HOME_RETAIL = "retail:home"
        CLOTHING_RETAIL = "retail:clothing"
        FURNITURE_RETAIL = "retail:furniture"
        ENTERTAINMENT_RETAIL = "retail:entertainment"
        DINING = "retail:dining"

        WHOLESALE = "wholesale:unspecified"
        FOOD_WHOLESALE = "wholesale:food"
        METAL_WHOLESALE = "wholesale:metal"
        PLASTIC_WHOLESALE = "wholesale:plastic"
        EQUIPMENT_WHOLESALE = "wholesale:equipment"
        ELECTRICAL_WHOLESALE = "wholesale:electrical"
        GLASS_WHOLESALE = "wholesale:glass"
        WOOD_WHOLESALE = "wholesale:wood"
        BUILDING_MATERIALS_WHOLESALE = "wholesale:building_materials"
        TEXTILE_WHOLESALE = "wholesale:textile"
        

        GOLD = "mine:gold"
        SILVER = "mine:silver"
        PLATINUM = "mine:platinum"
        LIMESTONE = "mine:limestone"
        COAL = "mine:coal"
        GRAVEL = "mine:gravel"
        SAND = "mine:sand"
        BAUXITE = "mine:bauxite"
        LITHIUM = "mine:lithium"
        URANIUM = "mine:uranium"
        POTASH = "mine:potash"
        SULFUR = "mine:sulfur"
        SALT = "mine:salt"
        RARE_EARTH = "mine:rare_earth"
        IRON = "mine:iron"
        COLTAN = "mine:coltan"

        PETROLEUM = "refinery:petroleum"
        METAL = "refinery:metal"        
        OTHER = "refinery:other"

        WATER_TREATMENT = "water:treatment"
        WATER_STORAGE = "water:storage"
        WATER_DESALINATION = "water:desalination"

        DRAYAGE = "logistics:drayage"
        DISTRIBUTION = "logistics:distribution"
        FOOD_DISTRIBUTION = "logistics:distribution:food"
        MEDICAL_DISTRIBUTION = "logistics:distribution:medical"
        BEVERAGE_DISTRIBUTION = "logistics:distribution:beverage"
        WAREHOUSING = "logistics:warehousing"
        HAULING = "logistics:hauling"

        STORAGE = "storage:unspecified"
        WASTE_STORAGE = "storage:waste"
        PERSONAL_STORAGE = "storage:personal"
        VEHICLE_STORAGE = "storage:vehicle"

        WASTE_DISPOSAL = "waste:disposal"
        WASTE_TREATMENT = "waste:treatment"
        SOLID_WASTE_TRANSFER = "waste:transfer"
        
        METAL_RECYCLING = "recycling:metal"
        PLASTIC_RECYCLING = "recycling:plastic"
        PAPER_RECYCLING = "recycling:paper"
        GLASS_RECYCLING = "recycling:glass"
        TEXTILE_RECYCLING = "recycling:textile"
        ELECTRONIC_RECYCLING = "recycling:electronic"
        OTHER_RECYCLING = "recycling:other"

    class FacilityProcess(str, Enum):
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
        ELECTROREFINING = "reaction:electrorefining"
        ELECTRODEPOSITION = "reaction:electrodeposition"
        GALVANIZING = "reaction:galvanizing"

        PACKING = "packing"
        BOXING = "packing:boxing"
        BOTTLE_FILLING = "packing:bottle_filling"

        REFRIGERATING = "climate_control:cooling:refrigerating"
        FREEZING = "climate_control:cooling:freezing"
        HEATING = "climate_control:heating"
        COOLING = "climate_control:cooling"
        DEHUMIDIFYING = "climate_control:dehumidifying"
        HUMIDIFYING = "climate_control:humidifying"

        MACHINING = "fabrication:machining"
        CNC = "fabrication:machining:cnc"
        CUTTING = "fabrication:machining:cutting"
        PLASMA_CUTTING = "fabrication:machining:cutting:plasma"
        LASER_CUTTING = "fabrication:machining:cutting:laser"
        WATERJET_CUTTING = "fabrication:machining:cutting:waterjet"
        GRINDING = "fabrication:machining:grinding"
        DRILLING = "fabrication:machining:drilling"
        MILLING = "fabrication:machining:milling"
        TURNING = "fabrication:machining:turning"
        FDM = "fabrication:additive:fdm"
        SLS = "fabrication:additive:sls"
        SLA = "fabrication:additive:sla"
        WELDING = "fabrication:welding"
        PAINTING = "fabrication:painting"
        COATING = "fabrication:coating"
        POWDER_COATING = "fabrication:coating:powder"        
        ASSEMBLY = "fabrication:assembly"
        CASTING = "fabrication:casting"
        FORGING = "fabrication:forging"
        INJECTION_MOLDING = "fabrication:injection_molding"
        FABRICATION = "fabrication:various"

        SHREDDING = "disassembly:shredding"
        METAL_SHREDDING = "disassembly:shredding:metal"
        PAPER_SHREDDING = "disassembly:shredding:paper"

        BULK_HANDLING = "handling:bulk"
        CONVEYOR_BELT = "handling:bulk:conveyor_belt"
        BUCKET_ELEVATOR = "handling:bulk:bucket_elevator"
        SCREW_CONVEYOR = "handling:bulk:screw_conveyor"
        VIBRATING_CONVEYOR = "handling:bulk:vibrating_conveyor"
        PNEUMATIC_CONVEYOR = "handling:bulk:pneumatic_conveyor"
        AERIAL_CONVEYOR = "handling:bulk:aerial_conveyor"
        DRAG_CHAIN_CONVEYOR = "handling:bulk:drag_chain_conveyor"
        FLUIDIZED_CONVEYOR = "handling:bulk:fluidized_conveyor"
        OTHER_CONVEYOR = "handling:bulk:other"

        GINNING = "textile:ginning"
        CARDING = "textile:carding"
        COMBING = "textile:combing"
        SPINNING = "textile:spinning"
        WINDING = "textile:winding"
        WARPING = "textile:warping"
        WEAVING = "textile:weaving"
        FINISHING = "textile:finishing"

        LINE_FISHING = "agriculture:fishing:line"
        NET_FISHING = "agriculture:fishing:net"
        TRAWLING = "agriculture:fishing:trawling"
        OTHER_FISHING = "agriculture:fishing:other"

        SOLAR_PV = "energy:generation:solar_pv"
        SOLAR_THERMAL = "energy:generation:solar_thermal"
        WIND = "energy:generation:wind_turbine"
        HYDRO = "energy:generation:water_turbine"
        GEOTHERMAL = "energy:generation:geothermal"
        BIOGAS = "energy:generation:biogas"
        BIODIESEL = "energy:generation:biodiesel"
        BIOETHANOL = "energy:generation:bioethanol"
        BIOMASS = "energy:generation:biomass"
        NUCLEAR_FISSION = "energy:generation:nuclear_fission"
        NUCLEAR_FUSION = "energy:generation:nuclear_fusion"
        COAL = "energy:generation:thermal:coal_combustion"
        NATURAL_GAS = "energy:generation:thermal:natural_gas_combustion"
        OIL = "energy:generation:thermal:oil_combustion"
        WOOD = "energy:generation:thermal:wood_combustion"
        STEAM = "energy:transformation:steam_engine"
        OTHER_FUEL = "energy:generation:thermal:other"



    observation_type: Literal['facility']
    description: str
    functions: Optional[FacilityFunction | list[FacilityFunction]]
    processes: Optional[FacilityProcess | list[FacilityProcess]]


class AgricultureObservation(Observation):
    """An observation of an agricultural activity -- e.g. a field of crops, a greenhouse, aquaculture, tree plantation etc."""

    class AgricultureType(str, Enum):
        CROP = "agriculture"
        FORESTRY = "forestry"
        ANIMAL_HUSBANDRY = "animal_husbandry"

    class CropType(str, Enum):
        CEREAL = "cereal[1]"
        WHEAT = "cereal:wheat[11]"
        MAIZE = "cereal:maize[12]"
        RICE = "cereal:rice[13]"
        SORGHUM = "cereal:sorghum[14]"
        BARLEY = "cereal:barley[15]"
        RYE = "cereal:rye[16]"
        OATS = "cereal:oats[17]"
        MILLET = "cereal:millet[18]"
        OTHER_CEREAL = "cereal:other[19]"
        VEGETABLES_AND_MELONS = "vegetables_melons[2]"
        LEAFY_VEGETABLES = "vegetables_melons:leafy[21]"
        FRUIT_BEARING_VEGETABLES = "vegetables_melons:fruit_bearing[22]"
        ROOT_VEGETABLES = "vegetables_melons:root[23]"
        MUSHROOMS = "vegetables_melons:mushrooms[24]"
        OTHER_VEGEATABLES = "vegetables_melons:other[25]"
        FRUIT_NUTS = "fruit_nuts[3]"
        TROPICAL_FRUIT = "fruit_nuts:tropical[31]"
        CITRUS = "fruit_nuts:citrus[32]"
        GRAPES = "fruit_nuts:grapes[33]"    
        BERRIES = "fruit_nuts:berries[34]"
        POMME_STONE = "fruit_nuts:pomme_stone[35]"
        NUTS = "fruit_nuts:nuts[36]"
        OTHER_FRUIT = "fruit_nuts:other[39]"
        OILSEEDS = "oilseeds[4]"
        SOYBEANS = "oilseeds:soybeans[41]"
        GROUNDNUTS = "oilseeds:groundnuts[42]"
        TEMPORARY_OILSEEDS = "oilseeds:temporary[43]"
        PERMANENT_OILSEEDS = "oilseeds:permanent[44]"
        ROOT_TUBER = "root_tuber[5]"
        POTATOES = "root_tuber:potatoes[51]"
        SWEET_POTATOES = "root_tuber:sweet_potatoes[52]"
        CASSAVA = "root_tuber:cassava[53]"
        YAMS = "root_tuber:yams[54]"
        OTHER_ROOT_TUBER = "root_tuber:other[55]"
        BEVERAGE_CROPS = "beverage_crops[61]"
        COFFEE = "beverage_crops:coffee[611]"
        TEA = "beverage_crops:tea[612]"
        MATE = "beverage_crops:mate[613]"
        OTHER_BEVERAGE_CROPS = "beverage_crops:other[619]"
        SPICE_CROPS = "spice_crops[62]"
        TEMPORARY_SPICE_CROPS = "spice_crops:temporary[621]"
        PERMANENT_SPICE_CROPS = "spice_crops:permanent[622]"
        LEGUMES = "legumes[7]"
        BEANS = "legumes:beans[71]"
        BROADBEANS = "legumes:broadbeans[72]"
        CHICKPEAS = "legumes:chickpeas[73]"
        COWPEAS = "legumes:cowpeas[74]"
        LENTILS = "legumes:lentils[75]"
        LUPINS = "legumes:lupins[76]"
        PEAS = "legumes:peas[77]"
        PIGEONPEAS = "legumes:pigeonpeas[78]"
        OTHER_LEGUMES = "legumes:other[79]"
        SUGAR_CROPS = "sugar_crops[8]"  
        SUGAR_BEET = "sugar_crops:sugar_beet[81]"
        SUGAR_CANE = "sugar_crops:sugar_cane[82]"
        SWEET_SORGHUM = "sugar_crops:sweet_sorghum[83]"
        OTHER_SUGAR_CROPS = "sugar_crops:other[89]"
        GRASSES = "grasses[91]"
        TEMPORARY_FIBER_CROPS = "temporary_fiber[921]"
        PERMANENT_FIBER_CROPS = "permanent_fiber[922]"
        MEDICINAL_CROPS = "medicinal_crops[93]"
        RUBBER = "rubber[94]"
        FLOWER_CROPS = "flower_crops[95]"
        TOBACCO = "tobacco[96]"
        OTHER_CROPS = "other_crops[99]"

    class LiveStockType(str, Enum):
        CATTLE = "cattle"
        SHEEP = "sheep"
        GOATS = "goats"
        SWINE = "swine"
        POULTRY = "poultry"
        CHICKENS = "poultry:chickens"
        TURKEYS = "poultry:turkeys"
        OTHER_POULTRY = "poultry:other"
        HORSES = "horses"
        OTHER_LIVESTOCK = "other_livestock"
    
    class TreeType(str, Enum):
        pass

    agriculture_type: AgricultureType
    product: CropType | LiveStockType | TreeType
    shape: Optional[FeatureCollection]


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
    shape: Optional[FeatureCollection]


class ExtentObservation(Observation):
    """An observation of a human-defined boundary or area"""

    class BoundaryType(str, Enum):
        SURVEYED_BOUNDARY = "surveyed_boundary"
        NATURAL_BOUNDARY = "natural_boundary"
        AGRICULTURE_BOUNDARY = "agriculture_boundary"
        BUILT_BOUNDARY = "built_boundary"
        ADMINISTRATIVE_BOUNDARY = "administrative_boundary"
        OTHER_BOUNDARY = "other_boundary"

    class LandUseType(str, Enum):
        OPEN_WATER = "water[11]"
        RIVER = "water:river[111]"
        LAKE = "water:lake[112]"
        RESERVOIR_POND = "water:reservoir_pond[113]"
        BEACH = "water:beach[114]"
        SHOAL = "water:shoal[115]"
        PERMANENT_SNOW_ICE = "permanent_snow_ice[12]"
        DEVELOPED_OPEN_SPACE = "developed:open_space[21]"
        PARK_REC_AREA = "developed:open_space:park_rec_area[211]"
        PAVED = "developed:open_space:paved[212]"
        DEVELOPED_LOW_INTENSITY = "developed:low_intensity[22]"
        DEVELOPED_MEDIUM_INTENSITY = "developed:medium_intensity[23]"
        DEVELOPED_HIGH_INTENSITY = "developed:high_intensity[24]"
        BARREN_LAND = "barren_land[31]"
        SAND = "barren_land:sand[311]"
        ROCK = "barren_land:rock[312]"
        DECIDUOUS_FOREST = "forest:deciduous[41]"
        EVERGREEN_FOREST = "forest:evergreen[42]"
        MIXED_FOREST = "forest:mixed[43]"
        SHRUB_SCRUB = "shrub_scrub[52]"
        GRASSLAND_HERBACEOUS = "herbaceous:grassland[71]"
        SEDGE_HERBACEOUS = "herbaceous:sedge[72]"
        LICHENS = "herbaceouslichens[73]"
        MOSS = "herbaceous:moss[74]"
        PASTURE_HAY = "agriculture:pasture_hay[81]"
        CULTIVATED_CROPS = "agriculture:cultivated_crops[82]"
        WOODED_WETLANDS = "wetlands:wooded[90]"
        HERBACEOUS_WETLANDS = "wetlands:herbaceous[95]"
        OTHER = "other[99]"

    observation_type: Literal['extent']
    description: Optional[str]
    extent_id: Optional[str]
    boundary_type: Optional[BoundaryType]
    landuse_type: LandUseType
    shape: FeatureCollection


class SourceType(str, Enum):
    DIRECT = "direct"
    SCRAPE = "scrape"
    ONLINE = "online"
    CAPTURE = "capture"
    OTHER = "other"


SomeObservation = AssetObservation | TransportObservation | FacilityObservation | ResourceObservation | ExtentObservation


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

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# -------------------------
# Customer
# -------------------------

class CustomerCreate(BaseModel):
    customer_code: str
    name: str | None = None


class CustomerRead(ORMModel):
    id: int
    customer_code: str
    name: str | None
    status: str


# -------------------------
# Tower
# -------------------------

class TowerCreate(BaseModel):
    tower_code: str
    name: str | None = None
    latitude: float
    longitude: float
    elevation_m: float | None = None


class TowerRead(ORMModel):
    id: int
    tower_code: str
    name: str | None
    latitude: float
    longitude: float
    elevation_m: float | None
    status: str


# -------------------------
# Sector
# -------------------------

class SectorCreate(BaseModel):
    sector_code: str
    tower_code: str
    azimuth_deg: float | None = None
    electrical_tilt_deg: float | None = None
    mechanical_tilt_deg: float | None = None


class SectorRead(ORMModel):
    id: int
    sector_code: str
    tower_id: int
    azimuth_deg: float | None
    electrical_tilt_deg: float | None
    mechanical_tilt_deg: float | None
    status: str


# -------------------------
# Cell
# -------------------------

class CellCreate(BaseModel):
    cell_id: str
    sector_code: str
    technology: str = "4G"
    pci: int | None = None
    earfcn: int | None = None
    band: str | None = None
    bandwidth_mhz: float | None = None


class CellRead(ORMModel):
    id: int
    cell_id: str
    sector_id: int
    technology: str
    pci: int | None
    earfcn: int | None
    band: str | None
    bandwidth_mhz: float | None
    status: str


# -------------------------
# Device
# -------------------------

class DeviceCreate(BaseModel):
    device_id: str
    customer_code: str
    current_cell_id: str | None = None
    model: str | None = None
    manufacturer: str | None = None
    software_version: str | None = None
    antenna_type: str | None = None


class DeviceRead(ORMModel):
    id: int
    device_id: str
    customer_id: int
    current_cell_id: int | None
    model: str | None
    manufacturer: str | None
    software_version: str | None
    antenna_type: str | None
    status: str


# -------------------------
# SIM
# -------------------------

class SIMCreate(BaseModel):
    sim_id: str
    device_id: str
    operator: str | None = None
    plan_type: str | None = None


class SIMRead(ORMModel):
    id: int
    sim_id: str
    device_id: int
    operator: str | None
    plan_type: str | None
    status: str
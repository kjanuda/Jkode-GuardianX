from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Customer, Device, SIM, Tower, Sector, Cell
from app.schemas.network import (
    CustomerCreate,
    CustomerRead,
    TowerCreate,
    TowerRead,
    SectorCreate,
    SectorRead,
    CellCreate,
    CellRead,
    DeviceCreate,
    DeviceRead,
    SIMCreate,
    SIMRead,
)


router = APIRouter(
    prefix="/api/v1",
    tags=["Network Core"],
)


# ============================================================
# CUSTOMER
# ============================================================

@router.post(
    "/customers",
    response_model=CustomerRead,
    status_code=status.HTTP_201_CREATED,
)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
):
    existing = db.scalar(
        select(Customer).where(
            Customer.customer_code == payload.customer_code
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Customer already exists",
        )

    customer = Customer(
        customer_code=payload.customer_code,
        name=payload.name,
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


@router.get(
    "/customers",
    response_model=list[CustomerRead],
)
def list_customers(
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Customer).order_by(Customer.id)
    ).all()


# ============================================================
# TOWER
# ============================================================

@router.post(
    "/towers",
    response_model=TowerRead,
    status_code=status.HTTP_201_CREATED,
)
def create_tower(
    payload: TowerCreate,
    db: Session = Depends(get_db),
):
    existing = db.scalar(
        select(Tower).where(
            Tower.tower_code == payload.tower_code
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Tower already exists",
        )

    tower = Tower(
        tower_code=payload.tower_code,
        name=payload.name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        elevation_m=payload.elevation_m,
    )

    db.add(tower)
    db.commit()
    db.refresh(tower)

    return tower


@router.get(
    "/towers",
    response_model=list[TowerRead],
)
def list_towers(
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Tower).order_by(Tower.id)
    ).all()


# ============================================================
# SECTOR
# ============================================================

@router.post(
    "/sectors",
    response_model=SectorRead,
    status_code=status.HTTP_201_CREATED,
)
def create_sector(
    payload: SectorCreate,
    db: Session = Depends(get_db),
):
    existing = db.scalar(
        select(Sector).where(
            Sector.sector_code == payload.sector_code
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Sector already exists",
        )

    tower = db.scalar(
        select(Tower).where(
            Tower.tower_code == payload.tower_code
        )
    )

    if tower is None:
        raise HTTPException(
            status_code=404,
            detail="Tower not found",
        )

    sector = Sector(
        sector_code=payload.sector_code,
        tower_id=tower.id,
        azimuth_deg=payload.azimuth_deg,
        electrical_tilt_deg=payload.electrical_tilt_deg,
        mechanical_tilt_deg=payload.mechanical_tilt_deg,
    )

    db.add(sector)
    db.commit()
    db.refresh(sector)

    return sector


@router.get(
    "/sectors",
    response_model=list[SectorRead],
)
def list_sectors(
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Sector).order_by(Sector.id)
    ).all()


# ============================================================
# CELL
# ============================================================

@router.post(
    "/cells",
    response_model=CellRead,
    status_code=status.HTTP_201_CREATED,
)
def create_cell(
    payload: CellCreate,
    db: Session = Depends(get_db),
):
    existing = db.scalar(
        select(Cell).where(
            Cell.cell_id == payload.cell_id
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Cell already exists",
        )

    sector = db.scalar(
        select(Sector).where(
            Sector.sector_code == payload.sector_code
        )
    )

    if sector is None:
        raise HTTPException(
            status_code=404,
            detail="Sector not found",
        )

    cell = Cell(
        cell_id=payload.cell_id,
        sector_id=sector.id,
        technology=payload.technology,
        pci=payload.pci,
        earfcn=payload.earfcn,
        band=payload.band,
        bandwidth_mhz=payload.bandwidth_mhz,
    )

    db.add(cell)
    db.commit()
    db.refresh(cell)

    return cell


@router.get(
    "/cells",
    response_model=list[CellRead],
)
def list_cells(
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Cell).order_by(Cell.id)
    ).all()


# ============================================================
# DEVICE
# ============================================================

@router.post(
    "/devices",
    response_model=DeviceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_device(
    payload: DeviceCreate,
    db: Session = Depends(get_db),
):
    existing = db.scalar(
        select(Device).where(
            Device.device_id == payload.device_id
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Device already exists",
        )

    customer = db.scalar(
        select(Customer).where(
            Customer.customer_code == payload.customer_code
        )
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    cell_db_id = None

    if payload.current_cell_id:
        cell = db.scalar(
            select(Cell).where(
                Cell.cell_id == payload.current_cell_id
            )
        )

        if cell is None:
            raise HTTPException(
                status_code=404,
                detail="Cell not found",
            )

        cell_db_id = cell.id

    device = Device(
        device_id=payload.device_id,
        customer_id=customer.id,
        current_cell_id=cell_db_id,
        model=payload.model,
        manufacturer=payload.manufacturer,
        software_version=payload.software_version,
        antenna_type=payload.antenna_type,
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    return device


@router.get(
    "/devices",
    response_model=list[DeviceRead],
)
def list_devices(
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Device).order_by(Device.id)
    ).all()


# ============================================================
# SIM
# ============================================================

@router.post(
    "/sims",
    response_model=SIMRead,
    status_code=status.HTTP_201_CREATED,
)
def create_sim(
    payload: SIMCreate,
    db: Session = Depends(get_db),
):
    existing = db.scalar(
        select(SIM).where(
            SIM.sim_id == payload.sim_id
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="SIM already exists",
        )

    device = db.scalar(
        select(Device).where(
            Device.device_id == payload.device_id
        )
    )

    if device is None:
        raise HTTPException(
            status_code=404,
            detail="Device not found",
        )

    existing_device_sim = db.scalar(
        select(SIM).where(
            SIM.device_id == device.id
        )
    )

    if existing_device_sim:
        raise HTTPException(
            status_code=409,
            detail="Device already has a SIM",
        )

    sim = SIM(
        sim_id=payload.sim_id,
        device_id=device.id,
        operator=payload.operator,
        plan_type=payload.plan_type,
    )

    db.add(sim)
    db.commit()
    db.refresh(sim)

    return sim


@router.get(
    "/sims",
    response_model=list[SIMRead],
)
def list_sims(
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(SIM).order_by(SIM.id)
    ).all()
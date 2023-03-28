from typing import Optional
import os
from datetime import datetime
import typer
from sqlalchemy import select, create_engine, insert, func
from sqlalchemy.orm import Session
from geoalchemy2 import Geometry
from geojson_pydantic.geometries import Point, Polygon
from shared.db import (
    Users,
    ObservationEvents,
    Observations,
    Entity,
    EntityObservation,
    EntityIdentifier,
)
from shared.util import canonicalize_identifier


DATABASE_URL = os.getenv("DB_CREDS")
engine = create_engine(DATABASE_URL)

app = typer.Typer()


@app.command()
def main():
    with Session(engine) as session:
        # Select all observations that do not have a link to an entity -- i.e., the outer join on the
        # EntityObservation table is NULL for that column.

        stmt = (
            select(
                Observations.id,
                Observations.observation_type,
                Observations.payload,
                EntityObservation.observation_id,
                EntityObservation.entity_id,
                ObservationEvents.location,
            )
            .outerjoin(EntityObservation)
            .join(ObservationEvents)
            .where(EntityObservation.observation_id.is_(None))
        )
        resp = session.execute(stmt)
        for r in resp.fetchall():
            process_observation(r, session)
        
        session.commit()


def process_observation(obs: Observations, session: Session):
    typer.echo(f"Processing observation {obs.id} ", nl=False)

    # check if the observation refers to an entity that already exists
    ent = find_entity(obs)

    # if the entity does not exist, create it
    if ent:
        typer.echo(f" | F {ent.id}")
    else:
        ent = create_entity_from_observation(obs, session)

    # link the observation to the entity and then (re-)synthesize the entity
    typer.echo(ent)
    add_observation_to_entity(obs, ent, session)
    synthesize_entity(ent, session)


def find_entity(obs) -> Optional[Entity]:
    obs_type = obs.observation_type
    obs_payload = obs.payload
    try:
        obs_location = (
            float(obs.location["latitude"]),
            float(obs.location["longitude"]),
        )
    except ValueError:
        typer.echo("Invalid location")
        return None

    # temp = select(Entity).where(func.)
    if obs_type == "facility":
        pass
    elif obs_type == "asset":
        if "asset_id" in obs_payload and "id_text" in obs_payload["asset_id"]:
            id_text = obs_payload["asset_id"].get("id_text", None)
            # typer.echo(f"Searching for asset entity with id {id_text}...", nl=False)
            stmt = (
                select(Entity, EntityIdentifier)
                .join(EntityIdentifier)
                .where(
                    EntityIdentifier.identifier_canonical == id_text
                    and Entity.entity_type == "asset"
                )
            )
            with engine.connect() as conn:
                res = conn.execute(stmt)
                entity = res.fetchone()
                if entity:
                    # typer.echo("FOUND")
                    return entity
                else:
                    # typer.echo("NOT FOUND")
                    return None
    return None


def create_entity_from_observation(obs, session: Session) -> Entity:
    # Create the entity and return it. This method assumes that the entity does not
    # exist, and will create a duplicate if it does.
    typer.echo(" | C", nl=False)
    ent: Entity = Entity(
        entity_type=obs.observation_type,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        shape=None,
        location=None,
        data={},
    )
    session.add(ent)
    session.flush()
    typer.echo(ent)
    return ent


def add_observation_to_entity(obs, ent: Entity, session: Session):
    # Create a link between the observation and the entity
    eo: EntityObservation = EntityObservation(
        entity_id=ent.id,
        observation_id=obs.id,
        created_at=datetime.now(),
        status="active",
    )
    session.add(eo)
    session.flush()


def synthesize_entity(ent: Entity, session: Session):
    # Synthesize the entity based on the linked observations. This operation
    # is idempotent, but the assumption is that an observation was just added
    # to the entity, so the entity should be re-synthesized.
    typer.echo(" | S")
    stmt = (
        select(Observations)
        .join(ObservationEvents)
        .join(EntityObservation)
        .join(Entity)
        .where(Entity.id == ent.id)
        .order_by(ObservationEvents.observed_at.desc())
    )
    res = session.execute(stmt).scalars()
    latest_obs_at = None
    latest_geo: Point = None
    data = {}

    for obs in res.all():
        if not latest_obs_at or obs.event.observed_at > latest_obs_at:
            latest_obs_at = obs.event.observed_at
        if obs.event.geo:
            latest_geo = obs.event.geo
        if obs.payload:
            data.update(obs.payload)

            if "asset_id" in obs.payload:
                asset_id = obs.payload["asset_id"]
                if "id_text" in asset_id:
                    id_text = asset_id["id_text"]
                    id_type = asset_id.get("id_type")
                    ent.identifiers.append(
                        EntityIdentifier(
                            identifier=id_text,
                            identifier_canonical=canonicalize_identifier(id_text),
                            issuer_type='operator',
                        )
                    )
    
    # for now, we just update the entity with the latest observation
    ent.latest_observation_at = latest_obs_at
    ent.updated_at = datetime.now()
    ent.data = data
    if latest_geo:
        ent.location = latest_geo
    session.flush()


if __name__ == "__main__":
    app()

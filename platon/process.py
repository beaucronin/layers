import os
import typer
from sqlalchemy import select, create_engine
from shared import Users
from shared.db import UserStats


DATABASE_URL = os.getenv("DB_CREDS")
engine = create_engine(DATABASE_URL)

app = typer.Typer()

@app.command()
def main():
    typer.echo("Hello World")
    typer.echo(UserStats)

if __name__ == "__main__":
    app()
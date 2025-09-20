import datetime
import os

# https://github.com/Hamuko/oblivionis/blob/master/oblivionis/storage.py

from peewee import (
    CharField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    Model,
    PostgresqlDatabase,
)

db = PostgresqlDatabase(
    "oblivionis",
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD"),
    host=os.environ.get("DB_HOST"),
)


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    id = CharField(primary_key=True, max_length=20)
    name = CharField()


class Game(BaseModel):
    name = CharField(unique=True)


class Activity(BaseModel):
    timestamp = DateTimeField(default=lambda: datetime.datetime.now(datetime.UTC))
    user = ForeignKeyField(User)
    game = ForeignKeyField(Game)
    seconds = IntegerField()

def connect_db():
    db.connect()
    db.create_tables([User, Game, Activity])
# Written by Stephen Fromm <sfromm gmail com>
# Copyright (C) 2018 Stephen Fromm
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import time
import logging
from collections import OrderedDict

from peewee import *

DB_PROXY = Proxy()

class Manager(object):

    def __init__(self):
        engine = os.environ.get("NOCOIN_DATABASE_ENGINE", "sqlite")
        name = os.environ.get("NOCOIN_DATABASE_NAME", ":memory:")

        if 'sqlite' in engine:
            database = SqliteDatabase(name, threadlocals=True)
        elif 'postgres' in engine:
            user = os.environ.get("NOCOIN_DATABASE_USER")
            password = os.environ.get("NOCOIN_DATABASE_PASSWORD")
            database = PostgresqlDatabase(name, user=user, password=password)
        else:
            database = None
        DB_PROXY.initialize(database)

        self.engine = engine
        self.name = name
        self.database = database
        try:
            self.database.connect()
            # http://docs.peewee-orm.com/en/latest/peewee/database.html?#additional-connection-initialization
            if 'sqlite' in self.engine:
                self.database.execute_sql("PRAGMA foreign_keys = ON")
        except OperationalError as e:
            logging.error("failed to open database %s", name)
            raise

    def save(self, modinst):
        modinst.save()

    def create_tables(self):
        Transaction.create_table(fail_silently=True)
        Block.create_table(fail_silently=True)
        Node.create_table(fail_silently=True)

class BaseModel(Model):

    class Meta:
        database = DB_PROXY


class Block(BaseModel):

    height         = IntegerField(unique=True)
    proof         = IntegerField()
    last_height    = IntegerField(unique=True, null=True)
    timestamp     = FloatField(default=time.time)
    hash          = CharField()
    previous_hash = CharField()

    class Meta:
        db_table = 'block'

    def __repr__(self):
        return "<Block('%s', '%s', '%s')>" % (self.height, self.proof, self.previous_hash)

    def to_dict(self):
        data = {
            'height'        : self.height,
            'proof'         : self.proof,
            'hash'          : self.hash,
            'previous_hash' : self.previous_hash,
            'last_block'    : self.last_block().id,
            'timestamp'     : self.timestamp,
            'transactions'  : list(),
        }
        for t in self.transactions:
            data['transactions'].append( t.to_dict() )
        return OrderedDict(sorted(data.items(), key=lambda t: t[0]))

    @classmethod
    def last_block(cls):
        l = Block.select().order_by(Block.height.desc()).limit(1)
        if l:
            return l[0]
        else:
            return None

    @classmethod
    def chain(cls):
        return Block.select().order_by(Block.height)

class Transaction(BaseModel):
    sender    = CharField()
    recipient = CharField()
    amount    = IntegerField()
    block     = ForeignKeyField(Block, related_name='transactions', null=False)

    class Meta:
        db_table = 'transaction'

    def __repr__(self):
        return "<Transaction('%s', '%s', '%s')>" % (self.sender, self.recipient, self.amount)

    def to_dict(self):
        data = {
            'sender'    : self.sender,
            'recipient' : self.recipient,
            'amount'    : self.amount,
        }
        return OrderedDict(sorted(data.items(), key=lambda t: t[0]))

class Node(BaseModel):

    uuid = CharField(unique=True)
    node = CharField(unique=True)

    class Meta:
        db_table = 'node'

    def __repr__(self):
        return "<Node('%s')>" % (self.node)

    def to_dict(self):
        data = {
            'node' : self.node,
            'uuid' : self.uuid,
        }
        return OrderedDict(sorted(data.items(), key=lambda t: t[0]))

    @classmethod
    def nodes(cls):
        return Node.select()


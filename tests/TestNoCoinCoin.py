import hashlib
import json
import logging
import os
from urllib.parse import urlparse

os.environ["NOCOIN_DATABASE_ENGINE"] = "sqlite"
os.environ["NOCOIN_DATABASE_NAME"] = ":memory:"

from nocoin import *
from nocoin.blockchain import *
from nocoin.model import *
from unittest import TestCase

logger = logging.getLogger()
logger.level = logging.INFO

class BlockChainTestCase(TestCase):

    def setUp(self):
        self.blockchain = Blockchain()

    def create_block(self, proof=123, previous_hash='abc'):
        self.blockchain.new_block(proof, previous_hash)

    def create_transaction(self, sender='a', recipient='b', amount=1):
        self.blockchain.new_transaction(
            sender=sender,
            recipient=recipient,
            amount=amount
        )

class TestBlockChain(BlockChainTestCase):

    def test_block_creation(self):
        self.create_block()

        last_block = self.blockchain.last_block()
        chain = self.blockchain.chain()

        assert last_block['index'] == len(chain) - 1
        assert last_block['timestamp'] is not None
        assert last_block['proof'] == 123
        assert last_block['previous_hash'] == 'abc'

    def test_create_transaction(self):
        self.create_transaction()

        transaction = self.blockchain.current_transactions

        assert transaction
        assert transaction[0]['sender'] == 'a'
        assert transaction[0]['recipient'] == 'b'
        assert transaction[0]['amount'] == 1

    def test_last_block(self):
        self.create_block()

        last_block = self.blockchain.last_block()
        chain = self.blockchain.chain()

        assert last_block['index'] == len(chain) - 1
        assert last_block == chain[-1]

    def test_last_transaction(self):
        self.create_transaction()

        created_transaction = self.blockchain.current_transactions

        assert len(self.blockchain.current_transactions) == 1
        assert created_transaction[0] is self.blockchain.current_transactions[-1]

    def test_hash_is_correct(self):
        self.create_block()

        last_block = self.blockchain.last_block()
        chain = self.blockchain.chain()
        last_block_json = json.dumps(self.blockchain.last_block(), sort_keys=True).encode()
        last_block_hash = hashlib.sha512(last_block_json).hexdigest()

        assert len(last_block_hash) == 128
        assert last_block_hash == self.blockchain.hash(last_block)

    def test_proof_of_work(self):
        last_block = self.blockchain.last_block()
        proof = self.blockchain.proof_of_work(last_block)

        self.create_transaction()

        last_hash = self.blockchain.hash(last_block)
        new_block = self.blockchain.new_block(proof, last_hash)

        assert new_block == self.blockchain.last_block()

class TestBlockChainNodes(BlockChainTestCase):

    def test_a_register_node(self):
        uri = "http://127.0.0.1:5000"
        self.blockchain.register_node(uri)
        nodes = self.blockchain.nodes()
        node = { 'node' : urlparse(uri).netloc }

        assert node in nodes

    def test_b_malformed_node(self):
        uri = "http//127.0.0.1:5000"
        self.blockchain.register_node(uri)
        nodes = self.blockchain.nodes()
        node = { 'node' : urlparse(uri).netloc }

        assert node not in nodes

    def test_c_node_idempotency(self):
        uri = "http://127.0.0.1:5000"
        self.blockchain.register_node(uri)
        self.blockchain.register_node(uri)
        nodes = self.blockchain.nodes()
        node = { 'node' : urlparse(uri).netloc }

        assert len(nodes) == 1

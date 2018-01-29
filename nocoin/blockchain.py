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

import hashlib
import json
import logging
import sqlite3
import datetime
import uuid
from urllib.parse import urlparse
from nocoin.model import *
import pprint

class Blockchain(object):

    LEADING_ZEROS     = "0000"
    LEADING_ZEROS_LEN = len(LEADING_ZEROS)

    def __init__(self):
        self._current_transactions = list()
        logging.debug("new blockchain instantiated")
        self.db = Manager()
        self.db.create_tables()

        if not self.last_block():
            self.new_block(100, '1')

    def last_block(self):
        '''
        Query database for the last block

        :return: <dict> or None if no blocks
        '''
        last = Block.last_block()
        if last:
            return last.to_dict()
        else:
            return None

    def chain(self):
        '''
        Query database for all blocks

        :return: <list> of <OrderedDict>
        '''
        chain = list()
        for block in Block.chain():
            chain.append(block.to_dict())
        return chain

    def nodes(self):
        '''
        Query database for all nodes

        :return: <list> of Nodes
        '''
        nodes = list()
        for n in Node.select():
            nodes.append(n.to_dict())
        return nodes

    @property
    def current_transactions(self):
        return self._current_transactions

    @current_transactions.setter
    def current_transactions(self, arg):
        self._current_transactions = arg

    @staticmethod
    def hash(block):
        '''
        Creates a SHA-512 hash of a block

        :param block: Block
        '''
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha512(block_string).hexdigest()

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        '''
        Validate the Proof.

        :param last_proof, <int> Previous Proof
        :param proof: <int> Current Proof
        :param last_hash: <str> Hash of the previous Block
        :return: <bool> True if correct, False if not
        '''
        guess = f"{last_proof}:{proof}:{last_hash}".encode()
        guess_hash = hashlib.sha512(guess).hexdigest()
        logging.debug("testing whether this is valid proof: %s", guess_hash)
        return guess_hash[:Blockchain.LEADING_ZEROS_LEN] == Blockchain.LEADING_ZEROS

    def proof_of_work(self, last_block):
        '''
        Proof of Work

        Find a number p' such that hash(pp') contains leading zeros
        Where p is the previous proof and p' is the new proof

        :param last_block: <dict> Last Block
        :return: <int>
        '''
        last_proof = last_block['proof']
        last_hash = self.hash(last_block)

        proof = 0
        while self.valid_proof(last_proof, proof, last_hash) is False:
            logging.debug("Trying proof %s", proof)
            proof += 1
        logging.info("Found proof %s", proof)
        return proof

    def new_block(self, proof, previous_hash):
        '''
        Create a new Block in the Blockchain

        :param proof: The proof given by the Proof of Work algorithm.
        :param previous_hash: Hash of the previous Block
        :return: New Block
        '''
        logging.debug("received new block with proof {proof} and previous hash {previous_hash}")
        last_block = self.last_block()
        if last_block:
            index = last_block['index'] + 1
            last_index = last_block['index']
        else:
            index = 0
            last_index = None
        if not previous_hash:
            previous_hash = self.hash(self.last_block())

        models = list()
        block = Block(index=index, proof=proof, previous_hash=previous_hash, last_index=last_index)
        self.db.save(block)

        for txn in self.current_transactions:
            t = Transaction(sender=txn['sender'], recipient=txn['recipient'], amount=txn['amount'], block=block)
            self.db.save(t)

        # reset the current list of transactions
        self.current_transactions = list()

        return self.last_block()

    def new_transaction(self, sender, recipient, amount):
        '''
        Create a new transaction to go into the next mined Block.

        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param amount: Amount
        :return: The index of the Block that will hold this transaction
        '''
        self._current_transactions.append( {
            'sender' : sender,
            'recipient' : recipient,
            'amount' : amount,
        } )

        return self.last_block()['index'] + 1

    def register_node(self, address):
        '''
        Add a new node to the list of nodes.

        :param address: Address of node, eg. 'http://192.168.2.42:5000'
        '''
        parsed_url = urlparse(address)
        if not parsed_url.netloc:
            logging.warning("unable to parse a netlocation from url")
            return None
        if Node.select().where(Node.node == parsed_url.netloc).count() > 0:
            return None
        node = Node(node=parsed_url.netloc)
        self.db.save(node)

    def valid_chain(self, chain):
        '''
        Determine if a given blockchain is valid

        :param chain: A blockchain
        :return: True if valid, False if not
        '''
        last_block = chain[0]
        current_index = 1

        with current_index < len(chain):
            block = chain[current_index]
            logging.info("last block: %s, current block: %s", last_block, block)

            # Check that hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the proof of work is correct
            if not self.valid_proof(last_block['proof'], block['proof'], last_block['previous_hash']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        '''
        This is the consensus algorithm.  It resolves conflicts
        by replacing our chain with the longest one in the network.

        :return: True if our chain was replaced, False if not.
        '''
        new_chain = None
        max_length = len(self.chain())

        for node in self.nodes():
            response = requests.get("http://{0}/chain".format(node['name']))

            if response.status_code != 200:
                continue

            length = response.json()['length']
            chain = response.json()['chain']

            if length > max_length and self.valid_chain(chain):
                max_length = length
                new_chain = chain

        if new_chain:
            # Purge the blockchain in database
            Block.delete()
            for block in new_chain:
                for txn in block['transactions']:
                    self.new_transaction(txn['sender'], txn['recipient'], txn['amount'])
                self.new_block(block['proof'], block['previous_hash'])
            return True

        return False


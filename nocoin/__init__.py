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

__name__    = "nocoincoin"
__version__ = 18.01
__author__  = "Stephen Fromm"
__email__   = "sfromm gmail com"

import hashlib
import json
import os
import time
import uuid

import requests
from flask import Flask, jsonify, request

import nocoin.blockchain
from  nocoin.model import *

app = Flask(__name__)

# Generate a globally unique address for the node
node_identifier = str(uuid.uuid4()).replace('-', '')

# Instantiate the blockchain
blockchain = nocoin.blockchain.Blockchain()

@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block()
    proof = blockchain.proof_of_work(last_block)

    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1
    )

    last_hash = blockchain.hash(last_block)
    new_block = blockchain.new_block(proof, last_hash)

    response = {
        'mesage' : "New block forged",
        'index' : new_block['index'],
        'transactions' : new_block['transactions'],
        'proof' : new_block['proof'],
        'previous_hash' : new_block['previous_hash'],
    }
    return jsonify(response), 200

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain'  : blockchain.chain(),
        'length' : len(blockchain.chain()),
    }
    return jsonify(response), 200

@app.route('/', methods=['GET'])
def hello():
    return jsonify({ "message": "hello", "chain": blockchain.chain }), 200


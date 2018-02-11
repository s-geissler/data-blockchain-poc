from hashlib import sha256
from time import time
import logging
import json
from textwrap import dedent
from uuid import uuid4
from flask import Flask, jsonify, request


logging.basicConfig(level=logging.INFO)

class Block:
    def __init__ (self, index, data, proof, previous_hash):
        self.index = index
        self.timestamp = time()
        self.data = data
        self.proof = proof
        self.previous_hash = previous_hash

    def getHash(self):
        return sha256(str(self.index) + str(self.timestamp) + str(self.data) + str(self.proof) + str(self.previous_hash)).hexdigest()

class Blockchain:
    def __init__(self, difficulty = 1):
        self.difficulty = difficulty

        genesis = Block(0, ["This is the just the beginning"], 47, 0)
        self.chain = [genesis]
        
        self.new_data = []

    def addBlock(self, proof):
        block = Block(self.getLastBlock().index + 1, self.new_data, proof, self.chain[-1].getHash())
        if block.getHash()[:self.difficulty] == "0" * self.difficulty:
            logging.debug("Block accepted! hash=" + block.getHash() + " proof=" + str(block.proof))
            self.chain.append(block)
            self.new_data = []
            return 0
        else:
            logging.debug("Block rejected! hash=" + block.getHash() + " proof=" + str(block.proof))
            return 1

    def addData(self, in_data):
        self.new_data.append(in_data)
        return len(self.chain) + 1

    def getLastBlock(self):
        return self.chain[-1]

    def validate(self):
        previous_block = self.chain[0]
        for block in self.chain[1:]:
            if previous_block.getHash() != block.previous_hash:
                logging.info("Validation failed! Manipulation of block " + str(previous_block.index))
                return 1
            previous_block = block
        logging.info("Validation passed! Everything is in order.")
        return 0

    def mineBlock(self):
        proof = 0
        while self.addBlock(proof):
            proof = proof + 1
        logging.info("New block found! hash=" + self.getLastBlock().getHash())
        return self.getLastBlock().index

app = Flask(__name__)

node_identifier = str(uuid4()).replace('-', '')

bc = Blockchain(4)

@app.route('/mine', methods=['GET'])
def mine():
    index = bc.mineBlock()
    return "We mined a new block (" + str(index) + ")"

@app.route('/data/add', methods=['POST'])
def add_data():
    values = request.get_json()

    required = ['in_data']

    if not values:
        return "Invalid Request", 400
    
    if not all(k in values for k in required):
        return "Missing Values", 400

    index = bc.addData(values['in_data'])
    response = {'message': 'Data will be added to block ' + str(index)}
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = []
    for block in bc.chain:
        response.append({"index": block.index, "hash": block.getHash(), "proof": block.proof})
    return jsonify(response), 200

@app.route('/validate', methods=['GET'])
def validate_chain():
    response = { 'code': bc.validate() }
    return jsonify(response), 200

@app.route('/block/get', methods=['POST'])
def get_block():
    values = request.get_json()

    required = ['index']

    if not values:
        return "Invalid Request", 400
    
    elif not all(k in values for k in required):
        return "Missing Values", 400

    elif values['index'] > bc.getLastBlock().index:
        return "Invalid Block", 400

    block = bc.chain[values['index']]

    response = { 'index': block.index,
                 'timestamp': block.timestamp,
                 'data': block.data,
                 'proof': block.proof,
                 'previous_hash': block.previous_hash }

    return jsonify(response), 200
                    
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

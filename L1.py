import json
import os
from web3 import Web3
import hashlib

web3 = None
chain_id = 31337

def load_abi(file: str):
    with open(file, "r") as f:
        return json.loads(f.read())['abi']

def interact_call(contract_address, abi, function_name: str, args: list):
    # Create contract instance at the deployed address
    contract = web3.eth.contract(address=contract_address, abi=abi)
    f = getattr(contract.functions, function_name)
    value = f(*args).call()

    return value

def interact_read(contract_address, abi, variable_name: str):
    contract = web3.eth.contract(address=contract_address, abi=abi)
    return contract.functions[variable_name].call()

def interact_transact(contract_address, abi, function_name: str, args: list, address, private_key, value: int = 0, overrideGas: int|None = None):
    # Create contract instance at the deployed address
    contract = web3.eth.contract(address=contract_address, abi=abi)

    if overrideGas is None:
        overrideGas = 10000000

    base_fee = web3.eth.get_block("latest")["baseFeePerGas"]
    priority_fee = Web3.to_wei(0.01, "gwei")  # your desired tip
    max_fee_per_gas = base_fee + priority_fee * 2
    
    txPreset = {
        "chainId": chain_id,
        "from": address,
        "value": value,  # Amount of ETH you want to send
        "nonce": web3.eth.get_transaction_count(address),
        # You can optionally set the gas limit and gas price, or leave it to be auto-calculated
        "gas": 1000000,  
        "maxFeePerGas": max_fee_per_gas,
        "maxPriorityFeePerGas": priority_fee,
        "type": 2,
    }
    print(f"Sending value {value}")

    tx = contract.functions[function_name](*args).build_transaction(txPreset)

    # Sign the transaction
    signed_tx = web3.eth.account.sign_transaction(tx, private_key=private_key)

    # Send the transaction
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

    # Wait for the transaction receipt
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

    decoded_events = []
    try:
        for event in contract.events:
            for log in tx_receipt.logs:
                try:
                    dec = event().process_log(log)
                    print(f"EMITTED: {dec['event']}: {dec['args']}")
                    decoded_events.append(dec)
                except:
                    pass
    except:
        print("Failed to decode events, maybe there are none?")

    # log the gas usage of this call
    log = f"Calling {function_name} on {contract_address} with args {args} took {tx_receipt.gasUsed} gas\n"
    with open('gaslog.txt', 'a') as f:
        f.write(log)

    if tx_receipt.status == 0:
        print("TX FAILED")
        assert False
    return tx_receipt, decoded_events

def interact_send(contract_address, value: int, address, private_key):
    # Prepare the transaction
    
    base_fee = web3.eth.get_block("latest")["baseFeePerGas"]
    priority_fee = Web3.to_wei(1, "gwei")  # your desired tip
    max_fee_per_gas = base_fee + priority_fee * 2
    
    tx = {
        "chainId": chain_id,
        "to": contract_address,
        "from": address,
        "value": value,  # Amount of ETH you want to send
        "nonce": web3.eth.get_transaction_count(address),
        # You can optionally set the gas limit and gas price, or leave it to be auto-calculated
        "gas": 1000000,  
        "maxFeePerGas": max_fee_per_gas,
        "maxPriorityFeePerGas": priority_fee,
        "type": 2,
    }
    print(f"SENDING {value} WEI")

    # Sign the transaction
    signed_tx = web3.eth.account.sign_transaction(tx, private_key=private_key)

    # Send the transaction
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

    # Wait for the transaction receipt
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

    print(f"Num of logs emitted are {tx_receipt.logs}")

    if tx_receipt.status == 0:
        print("TX FAILED")
        assert False

    return tx_receipt

class L1Identity():
    def __init__(self, address):
        self.address = address

    def _balance(self):
        return web3.eth.get_balance(self.address)
    
    def print_balance(self):
        balance = self._balance()
        print(f"Balance of {self.address}: {balance / 1e18} ETH ({balance})")

class OwnedL1Identity(L1Identity):
    def __init__(self, private_key):
        self.private_key = private_key

        account = web3.eth.account.from_key(private_key)
        super().__init__(account.address)

class Contract():
    def __init__(self, contract_address, contract_abi):
        global web3
        self.address = contract_address
        self.abi = contract_abi
        self.contract = web3.eth.contract(address=contract_address, abi=contract_abi)

    def _interact(self, user: OwnedL1Identity, method: str, args: list = [], value: int = 0, overrideGas: int|None = None):
        return interact_transact(self.address, self.abi, method, args, user.address, user.private_key, value, overrideGas)
    
    def _send(self, user: OwnedL1Identity, value: int = 0):
        return interact_send(self.address, value, user.address, user.private_key)
    
    def _call(self, method: str, args: list = []):
        return interact_call(self.address, self.abi, method, args)

    def _read(self, variable: str):
        return interact_read(self.address, self.abi, variable)
    
    def _balance(self):
        return web3.eth.get_balance(self.address)
    
    def _storage(self, slot: int):
        return web3.eth.get_storage_at(self.address, slot)
    
    def _storagedump(self, slots: int):
        print(f"Dumping storage for contract {self.address}:")
        for slot in range(slots):
            print(f" {slot}: {self._storage(slot).hex()}")
    
    def as_object(self) -> dict:
        return {'address': self.address, 'abi': self.abi, 'type': 'Contract'}
    
    def decode_logs(self, logs: list): # TODO: Make this better
        ret = []
        for event in self.contract.events:
            for log in logs:
                try:
                    dec = event().process_log(log)
                    ret.append(dec)
                except:
                    pass
        # NOTE: Keep in mind that this contract might not be able to decode all events of a transaction! 
        #  It might be the case that some events have been emitted by other contracts.
        return ret
    
    def __repr__(self):
        return f"<Contract @{self.address}>"
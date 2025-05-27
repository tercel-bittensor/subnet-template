import bittensor as bt
from protocol import Dummy
import argparse

wallet = bt.wallet(name="owner", hotkey="miner_hotkey")

parser = argparse.ArgumentParser()
bt.subtensor.add_args(parser)
config = bt.config(parser)
config.subtensor.network = "local"
config.subtensor.chain_endpoint = "ws://127.0.0.1:9944"

subtensor = bt.subtensor(config=config)
netuid = 2
metagraph = subtensor.metagraph(netuid)
metagraph.sync()

target_hotkey = "5GGocSghh9HYV3F6ZEEEWnYzg3E6fLEWmUp6jiFNntq9yJKd"
print("local chain metagraph.hotkeys:", metagraph.hotkeys)

if target_hotkey not in metagraph.hotkeys:
    print(f"target hotkey {target_hotkey} not in metagraph.hotkeys, please check netuid, node registration and chain synchronization.")
    exit(1)

uid = metagraph.hotkeys.index(target_hotkey)
dendrite = bt.dendrite(wallet=wallet)
synapse = Dummy(dummy_input=123)

# get target axon
target_axon = metagraph.axons[uid]

# only query one miner
responses = dendrite.query(
    axons=[target_axon],
    synapse=synapse,
    timeout=12
)

print("Response from miner:", responses[0].dummy_output)
# Polkadot monitoring service

Set of prometheus exporters designed to track the performance of validators in the Polkadot and Kusama networks.

#### How to start

1. Install Docker and Docker Compose from https://docs.docker.com/engine/install/ or any other compose compatible tool and container runtime

2. Add RPC endpoints to config files `polkadot.env` and `kusama.env` in the following format:

```
WS_ENDPOINT="ws://your-node1:9944"
RPC_ENDPOINTS="http://your-node1:9933,http://your-node2:9933,http://your-node3:9933/"
```

3. Run the project:
    * `docker-compose -f docker-compose.yml -f polkadot.yml -f kusama.yml up -d`-  will start exporters for polkadot and kusama
    * `docker-compose -f docker-compose.yml -f polkadot.yml` - will start expoters only for polkadot
    * `docker-compose -f docker-compose.yml -f kusama.yml` - will start expoters only for kusama

4. Inspect the [dashboard](http://127.0.0.1:3000/d/fDrj0_EGz/p2p-org-polkadot-kusama-dashboard?orgId=1) (default username and password `admin`, `admin`)


#### Notes

* Finality expoter metrics `polkadot_finality_prevotes`, `polkadot_finality_precommits` are probablistic because data from `grandpa_roundState` call is instant and it depends when RPC call actually occurs in the begining of the round or at the end of the round. The more measurements (more RPC nodes present in config) than more accurate will be exposed metric
# Polkadot monitoring service
Set of prometheus exporters designed to track the performance of validators in the Polkadot and Kusama networks.

#### How to start

1. Install Docker and Docker Compose from https://docs.docker.com/engine/install/ or any other compose compatible tool and container runtime

2. (Optional) Add RPC endpoints to config files `polkadot.env` and `kusama.env` in the following format:

```
WS_ENDPOINT="ws://your-node1:9944"
WS_ENDPOINTS="http://your-node1:9944,http://your-node2:9944,http://your-node3:9944/"
```

3. Run the project:
    * via make:
        * `make` - start both polkadot and kusama exporters
        * `make polkadot` - start only polkadot part
        * `make kusama` - start only kusama part
        * `make clean` - stop and destory
    * directly via docker-compose:
        * `docker-compose -f docker-compose.yml -f polkadot.yml -f kusama.yml up`-  will start exporters for polkadot and kusama
        * `docker-compose -f docker-compose.yml -f polkadot.yml up` - will start exporters only for polkadot
        * `docker-compose -f docker-compose.yml -f kusama.yml up` - will start exporters only for kusama

4. Inspect the [dashboard](http://127.0.0.1:3000/d/fDrj0_EGz/p2p-org-polkadot-kusama-dashboard?orgId=1) (default username and password `admin`, `admin`)

#### References
* https://github.com/polkascan/py-substrate-interface - Python Substrate Interface. Many thanks to `Stichting Polkascan (Polkascan Foundation)` for amazing library implimentation which successfully used in exporters.
* https://github.com/itering/scale.go - Go implementation of scale codec
* https://wiki.polkadot.network/ - Polkadot Wiki
* https://polkadot.js.org/docs/ - Good to know

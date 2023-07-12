

#### Project overview

Project build on top of the well known open-source monitoring solutions: Prometheus, Grafana and represents a set of exporters. Each exporter is independent and can be deployed into existing prometheus-compatible infrastructure. In this guide we will desribe different components of the system


#### Exporters

Each exporter is docker container. Exporter responsible for reading on-chain data and exposing prometheus metrics

##### common-exporter

Main exporter provide variety of metrics about validators performance.

Configuration (environment variables):

* `LISTEN` - ip to bind to or 0.0.0.0 to listen all interfaces
* `PORT` - port for exposed metrics
* `CHAIN` - scraping chain name: polkadot or kusama
* `WS_ENDPOINT` - URL of RPC node for example "wss://rpc.polkadot.io"

Build:

```
cd exporters/common
docker build . -f Dockerfile --build-arg exporter=common_exporter
```

##### finality-exporter

intensivly polls rpc method `grandpa_roundState` and calculates grandpa round participation ratio for each validator

Configuration (environment variables):

* `LISTEN` - ip to bind to or 0.0.0.0 to listen all interfaces
* `PORT` - port for exposed metrics
* `CHAIN` - scraping chain name: polkadot or kusama
* `WS_ENDPOINT` - URL of RPC node for example "wss://rpc.polkadot.io"
* `RPC_ENDPOINTS` - comma-separated list of distinct nodes to poll grandpa_roundState


Build:

```
cd exporters/common
docker build . -f Dockerfile --build-arg exporter=finality_exporter
```

##### events-exporter

follows head and counts occured on-chain events 

Configuration (environment variables):

* `WS_ENDPOINT` - URL of RPC node for example "wss://rpc.polkadot.io"
* `LISTEN` - "IP:PORT" to listen
* `LOG_LEVEL`- log verbosity, one of: debug,info,warn,error
* `NEW_HEAD_BY` - defines how exporter should detect new head, values: poll,subscription
* `EXPOSE_ID` - bool variable if exporter should try resolve validators identity as label or not

Build:

```
cd exporters/events
docker build . -f Dockerfile
```



#### Project overview

Project build on top of the well known open-source monitoring solutions: Prometheus, Grafana and represents a set of exporters. Each exporter is independent and can be deployed into existing prometheus-compatible infrastructure. In this guide we will desribe different components of the system


#### Exporters

Each exporter is docker container. Exporter responsible for reading on-chain data and exposing prometheus metrics

##### common-exporter

Main exporter provide variety of metrics about validators performance.

Exposed metrics:

* `polkadot_staking_currentEra`(chain) Current era
* `polkadot_staking_eraProgress`(chain) Era progress in percents
* `polkadot_staking_totalPoints`(chain) Amount of points earned by whole network
* `polkadot_staking_eraPoints`(chain,account) Amount of points earned by validator in current era
* `polkadot_staking_validatorsChart`(chain,account) Validator's position from best to worst
* `polkadot_session_currentSession`(chain) Current session index
* `polkadot_session_sessionProgress`(chain) Session progress in percents
* `polkadot_session_validators`(chain,account) Is validator active or not
* `polkadot_session_paraValidators`(chain,account) Paravalidator or not
* `polkadot_pv_pointsMedian`(chain,account) Median ParaValidator points ratio
* `polkadot_pv_pointsAverage`(chain,account) Average ParaValidator points ratio
* `polkadot_pv_pointsP95`(chain,account) ParaValidator points ration 95 percentile
* `polkadot_pv_eraPoints`(chain,account) Amount of points earned by ParaValidator in current session
* `polkadot_pv_paraValidatorsChart`(chain,account) ParaValidator's position from best to worst

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

Exposed metrics:

* `polkadot_finality_roundProcessed`(chain) Processed round - Rounds processed
* `polkadot_finality_prevotes`(chain,account) - Amount of prevoutes successed by validators
* `polkadot_finality_precommits`(chain,account) - Amount of precommits succesed by validators (became to 2/3)

`polkadot_finality_prevotes`, `polkadot_finality_precommits` are probablistic because data from `grandpa_roundState` call is instant and it depends when RPC call actually occurs in the begining of the round or at the end of the round. The more measurements (more RPC nodes present in config) than more accurate will be exposed metric

Configuration (environment variables):

* `LISTEN` - ip to bind to or 0.0.0.0 to listen all interfaces
* `PORT` - port for exposed metrics
* `CHAIN` - scraping chain name: polkadot or kusama
* `WS_ENDPOINTS` - comma-separated list of distinct nodes to poll grandpa_roundState example "wss://rpc.polkadot.io"

Build:

```
cd exporters/common
docker build . -f Dockerfile --build-arg exporter=finality_exporter
```

##### events-exporter

follows head and counts occured on-chain events 

Exposed metrics:

* `polkadot_events`(chain,module,method) - Occured on-chain events counter
* `polkadot_events_by_account`(chain,module,method,account) - Occured on-chain events with validator account
    * Event examples `Balances.Deposit`, `Balances.Locked`, `Balances.Reserved`, `Balances.Transfer`, `Balances.Unlocked`, `Balances.Upgraded`, `Balances.Withdraw`, `ImOnline.SomeOffline`, `Proxy.ProxyAdded`, `Staking.Bonded`, `Staking.Chilled`, `Staking.PayoutStarted`, `Staking.Rewarded`, `Staking.SlashReported`, `Staking.Unbonded`, `Staking.ValidatorPrefsSet`, `Staking.Withdrawn`, `TransactionPayment.TransactionFeePaid`, `VoterList.Rebagged`, `VoterList.ScoreUpdated`
    * `ParasDisputes.DisputeConcluded` - accounts considering candidate is Invalid, but majority conclusion = Valid

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

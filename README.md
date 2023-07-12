# Polkadot monitoring service
Set of prometheus exporters designed to track the performance of validators in the Polkadot and Kusama networks.


#### Many thanks
To `Stichting Polkascan (Polkascan Foundation)` for amazing library implimentation https://github.com/polkascan/py-substrate-interface which succefuly used in exporters.


#### Metics definition
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
* `polkadot_finality_roundProcessed`(chain) Processed round - Rounds processed
* `polkadot_finality_prevotes`(chain,account) - Amount of prevoutes successed by validators
* `polkadot_finality_precommits`(chain,account) - Amount of precommits succesed by validators (became to 2/3)
* `polkadot_events`(chain,module,method) - Occured on-chain events counter
* `polkadot_events_by_account`(chain,module,method,account) - Occured on-chain events with validator account
    * `{method="DisputeConcluded",module="ParasDisputes"}` - accounts considering candidate is Invalid, but majority conclusion = Valid

#### How to start

1. Install Docker and Docker Compose from https://docs.docker.com/engine/install/ or any other compose compatible tool and container runtime

2. Add RPC endpoints to config files `polkadot.env` and `kusama.env` in the following format:

```
WS_ENDPOINT="ws://your-node1:9944"
RPC_ENDPOINTS="http://your-node1:9933,http://your-node2:9933,http://your-node3:9933/"
```

3. Run the project:
    * `docker-compose -f docker-compose.yml -f polkadot.yml -f kusama.yml up -d`-  will start exporters for polkadot and kusama
    * `docker-compose -f docker-compose.yml -f polkadot.yml` - will start exporters only for polkadot
    * `docker-compose -f docker-compose.yml -f kusama.yml` - will start exporters only for kusama

4. Inspect the [dashboard](http://127.0.0.1:3000/d/fDrj0_EGz/p2p-org-polkadot-kusama-dashboard?orgId=1) (default username and password `admin`, `admin`)


#### Notes

* Finality exporter metrics `polkadot_finality_prevotes`, `polkadot_finality_precommits` are probablistic because data from `grandpa_roundState` call is instant and it depends when RPC call actually occurs in the begining of the round or at the end of the round. The more measurements (more RPC nodes present in config) than more accurate will be exposed metric


#### References
* https://github.com/polkascan/py-substrate-interface - Python Substrate Interface
* https://github.com/itering/scale.go - Go implementation of scale codec
* https://wiki.polkadot.network/ - Polkadot Wiki
* https://polkadot.js.org/docs/ - Good to know

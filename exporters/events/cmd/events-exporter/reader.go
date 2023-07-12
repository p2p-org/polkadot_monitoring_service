package main

import (
	"context"
	"encoding/json"
	"strings"
	"substrate-events-exporter/internal/client"
	"substrate-events-exporter/internal/decoder"
	"substrate-events-exporter/internal/dto"
	"substrate-events-exporter/internal/monitoring"
	"sync"
	"sync/atomic"
	"time"

	"github.com/sirupsen/logrus"
)

type contextKey string

const (
	ContextKeyBlockHash = contextKey("hash")
)

type Config struct {
	WSUrl             string `json:"WS_ENDPOINT" envconfig:"WS_ENDPOINT" default:"wss://rpc.polkadot.io/"`
	MetricsListen     string `json:"LISTEN" envconfig:"LISTEN" default:":9150"`
	LabelChainValue   string `json:"LABEL_CHAIN" envconfig:"LABEL_CHAIN" default:""`
	LogLevel          string `json:"LOG_LEVEL" envconfig:"LOG_LEVEL" default:"info"`
	NewHeadBy         string `json:"NEW_HEAD_BY" envconfig:"NEW_HEAD_BY" default:"poll"`
	ExposeIdentities  bool   `json:"EXPOSE_ID" envconfig:"EXPOSE_ID"`
	KnownValidatorCfg string `json:"VALIDATORS_CFG" envconfig:"VALIDATORS_CFG" default:""`
}

/*
```
validators:

	human-readable-hostname:
	  account: Das1dfiejn....

```
*/
type ValidatorsRegistry struct {
	Validators map[string]ValidatorRecord `yaml:"validators" json:"validators"`
}
type ValidatorRecord struct {
	AccountSS58 string `yaml:"account" json:"account"`
}

type EventsReader struct {
	wsclient              *client.RPCClient
	decoder               *decoder.Decoder
	log                   *logrus.Logger
	paraSessionValidators sync.Map //map[uint32][]string
	sessionValidators     sync.Map //map[uint32][]string
	cfg                   Config
	identities            map[string]string
	registry              *ValidatorsRegistry
	mon                   monitoring.Observer
	EventsProcessed       atomic.Int64
	EventsRate            int64
	LastProcessedHeight   uint64
}

func NewEventsReader(l *logrus.Logger, cfg Config, ctx context.Context) (*EventsReader, error) {
	wsclient := client.NewRPCClient(l, cfg.WSUrl)
	metadataRaw, err := wsclient.StateGetMetadata(ctx)
	if err != nil {
		return nil, err
	}
	decoder, err := decoder.NewDecoder(l, metadataRaw)
	if err != nil {
		return nil, err
	}

	r := EventsReader{
		decoder:             decoder,
		wsclient:            wsclient,
		LastProcessedHeight: 0,
		identities:          make(map[string]string),
		log:                 l,
		cfg:                 cfg,
	}
	if cfg.KnownValidatorCfg != "" {
		r.ReadKnownValidatorsFile(cfg.KnownValidatorCfg)
	}

	return &r, nil
}

func (reader *EventsReader) processSingleBlock(ctx context.Context, hash string) error {
	r, _ := reader.decoder.NewStorageRequest("system", "events")
	ctx, cancel := context.WithTimeout(ctx, 120*time.Second)
	defer cancel()
	eventsRaw, err := reader.wsclient.StateGetStorage(ctx, r, hash)
	if err != nil {
		reader.log.WithError(err).Warn("unable to read storage system_events")
		return err
	}
	events := reader.decoder.DecodeEvents(ctx, eventsRaw)
	if events != nil {
		blockCtx := context.WithValue(ctx, ContextKeyBlockHash, hash)
		var (
			dispEvents []dto.Event
		)
		for i := 0; i < len(events); i++ {
			switch {
			case events[i].Type.ModuleId == "ParasDisputes" && events[i].Type.EventId == "DisputeConcluded":
				conclustion := events[i].Params.([]interface{})
				if dto.MustMap(conclustion[1]).MustString("value") == "Valid" {
					dispEvents = append(dispEvents, events[i])
				}
			}
			reader.mon.ProcessEvent(MetricChainEventsCount, 1, reader.LabelValues(events[i].Type.ModuleId, events[i].Type.EventId, "")...)

		}
		reader.HandleDisputesConcluded(blockCtx, dispEvents)
		reader.HandleAllEvents(blockCtx, events)
		reader.EventsProcessed.Add(int64(len(events)))
	}
	return nil
}

func (reader *EventsReader) followHeadHashes(parentCtx context.Context, kind string) (chan string, chan error) {
	hashes := make(chan string)
	errs := make(chan error, 1)
	if kind == "subscription" {
		go func() {
			defer close(hashes)
			defer close(errs)
			frames, failures := reader.wsclient.ChainSubscribeNewHead(parentCtx)
			for {
				select {
				case f := <-frames:
					hashes <- dto.MustMap(f.Params).Get("result").MustString("parentHash")
				case e := <-failures:
					errs <- e
					return
				}
			}
		}()
	} else {
		ticker := time.NewTicker(15 * time.Second)
		go func() {
			defer close(hashes)
			defer close(errs)
			for range ticker.C {
				ctx, cancel := context.WithTimeout(parentCtx, 30*time.Second)
				header, err := reader.wsclient.ChainGetHeader(ctx, "")
				cancel()
				if err != nil {
					errs <- err
					return
				}
				if reader.LastProcessedHeight == 0 {
					reader.LastProcessedHeight = header.MustInt("number") - 1
				}
				for i := reader.LastProcessedHeight + 1; i <= header.MustInt("number"); i++ {
					ctx, cancel := context.WithTimeout(parentCtx, 30*time.Second)
					hash, err := reader.wsclient.ChainGetBlockHash(ctx, i)
					cancel()
					if err != nil {
						errs <- err
						return
					}
					hashes <- hash
					reader.LastProcessedHeight = i
				}
			}
		}()
	}
	return hashes, errs
}

func (reader *EventsReader) Read(parentctx context.Context) error {
	ticker := time.NewTicker(time.Minute)
	reader.EventsRate = 1
	go func() {
		counters := [3]int64{0, 0, 0}
		for range ticker.C {
			counters[0] = counters[1]
			counters[1] = counters[2]
			counters[2] = reader.EventsProcessed.Load()
			reader.EventsRate = (counters[2] - counters[0]) / 3
			reader.log.Infof("exporters average events rate %d/min", reader.EventsRate)
		}
	}()

	for {
		hashes, errs := reader.followHeadHashes(parentctx, reader.cfg.NewHeadBy)
	nested:
		for {
			select {
			case h := <-hashes:
				go reader.processSingleBlock(parentctx, h)
			case e := <-errs:
				reader.log.WithError(e).Warn("read loop will be restarted")
				time.Sleep(3 * time.Second)
				break nested
			case <-parentctx.Done():
				reader.log.Warn("exit")
				return parentctx.Err()
			}
		}
	}
}

func (reader *EventsReader) HandleDisputesConcluded(ctx context.Context, events []dto.Event) {
	if len(events) == 0 {
		return
	}
	// event itself does not contain accounts we need to extract extrinsics
	extrinsicIdxs := make(map[int]byte)
	for _, e := range events {
		extrinsicIdxs[e.ExtrinsicIdx] = 1
	}
	if ctx.Value(ContextKeyBlockHash) == nil {
		reader.log.Warn("wrong context")
		return
	}
	blockHash, _ := ctx.Value(ContextKeyBlockHash).(string)

	block, err := reader.wsclient.ChainGetBlock(ctx, blockHash)
	if err != nil {
		reader.log.WithField("block", blockHash).WithError(err).Warn("unable to read block due to transport issues")
		return
	}

	for k := range extrinsicIdxs {
		if k >= len(block.Extrinsics) {
			reader.log.Warn("extrinsic index out of range")
			continue
		}
		ext := reader.decoder.DecodeExtrinsic(ctx, block.Extrinsics[k])
		if ext == nil {
			continue
		}
		for _, v := range ext.GetSlice("params") {
			for _, disp := range v.Get("value").GetSlice("disputes") {
				session := uint32(disp.MustInt("session"))
				// https://paritytech.github.io/polkadot/book/types/disputes.html
				// struct DisputeStatementSet {
				//    candidate_hash: CandidateHash,
				//    session: SessionIndex,
				//    statements: Vec<(DisputeStatement, ValidatorIndex, ValidatorSignature)>,
				// }
				for _, stmt := range disp.GetSlice("statements") {
					status := stmt.Get("col1")                // DisputeStatement
					validatorIdx := int(stmt.MustInt("col2")) // ValidatorIndex
					if _, ok := status["Invalid"]; ok {
						accU32 := reader.GetParaSessionValidatorBy(ctx, session, validatorIdx)
						reader.mon.ProcessEvent(MetricChainEventsByAccountCount, 1, reader.LabelValues("ParasDisputes", "DisputeConcluded", accU32)...)
					}
				}
			}
		}
	}
}

func (reader *EventsReader) HandleAllEvents(ctx context.Context, events []dto.Event) {
	if len(events) == 0 {
		return
	}
	accsU32 := reader.GetSessionValidators(ctx, 0)
	var accsSS58 []string
	for i := 0; i < len(accsU32); i++ {
		accsSS58 = append(accsSS58, reader.decoder.SS58Encode(accsU32[i]))
		accsU32[i] = strings.TrimPrefix(accsU32[i], "0x")
	}
	for _, e := range events {
		raw, err := json.Marshal(e)
		if err == nil {
			for i := 0; i < len(accsSS58); i++ {
				if strings.Contains(string(raw), accsSS58[i]) || strings.Contains(string(raw), accsU32[i]) {
					reader.mon.ProcessEvent(MetricChainEventsByAccountCount, 1, reader.LabelValues(e.Type.ModuleId, e.Type.EventId, accsU32[i])...)
					break
				}
			}
		}
	}
}

// TODO: cleanup
func (reader *EventsReader) GetParaSessionValidators(ctx context.Context, session uint32) []string {
	blockHash, _ := ctx.Value(ContextKeyBlockHash).(string)
	if _, ok := reader.paraSessionValidators.Load(session); !ok {
		req, _ := reader.decoder.NewStorageRequest("paraSessionInfo", "accountKeys", session)
		resp, err := reader.wsclient.StateGetStorage(ctx, req, blockHash)
		if err != nil {
			reader.log.WithError(err).Warn("unable to read parasession validators")
		}
		sv := req.DecodeResponse(resp)
		if sv != nil {
			var paraSessionValidators []string
			for _, validator := range sv.([]interface{}) {
				paraSessionValidators = append(paraSessionValidators, validator.(string))
			}
			reader.paraSessionValidators.Store(session, paraSessionValidators)
		}
	}
	if pv, ok := reader.paraSessionValidators.Load(session); ok {
		return pv.([]string)
	}
	return nil
}

func (reader *EventsReader) GetParaSessionValidatorBy(ctx context.Context, session uint32, idx int) string {

	validators := reader.GetParaSessionValidators(ctx, session)
	if idx > len(validators) {
		return "Unknown"
	}
	return validators[idx]
}

// TODO: cleanup
func (reader *EventsReader) GetSessionValidators(ctx context.Context, session uint32) []string {
	blockHash, _ := ctx.Value(ContextKeyBlockHash).(string)
	if session == 0 {
		reader.sessionValidators.Range(func(key, value any) bool {
			i := key.(uint32)
			if i > session {
				session = i
			}
			return true
		})
	}
	if _, ok := reader.sessionValidators.Load(session); !ok {
		req, _ := reader.decoder.NewStorageRequest("session", "validators")
		resp, err := reader.wsclient.StateGetStorage(ctx, req, blockHash)
		if err != nil {
			reader.log.WithError(err).Warn("unable to read session validators", err)
		}
		sv := req.DecodeResponse(resp)
		if sv != nil {
			var sessionValidators []string
			for _, validator := range sv.([]interface{}) {
				sessionValidators = append(sessionValidators, validator.(string))
			}
			reader.sessionValidators.Store(session, sessionValidators)
		}
	}
	if sv, ok := reader.sessionValidators.Load(session); ok {
		return sv.([]string)
	}
	return nil
}

func (reader *EventsReader) GetSessionValidatorBy(ctx context.Context, session uint32, idx int) string {

	validators := reader.GetSessionValidators(ctx, session)
	if idx > len(validators) {
		return "Unknown"
	}
	return validators[idx]
}

package main

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"substrate-events-exporter/internal/client"
	"substrate-events-exporter/internal/decoder"
	"substrate-events-exporter/internal/dto"
	"substrate-events-exporter/internal/monitoring"
	"sync"
	"sync/atomic"
	"time"

	"github.com/sirupsen/logrus"
	"golang.org/x/sync/errgroup"
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

type HeadReader struct {
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

func NewHeadReader(l *logrus.Logger, cfg Config, ctx context.Context) (*HeadReader, error) {
	wsclient := client.NewRPCClient(l, cfg.WSUrl)
	metadataRaw, err := wsclient.StateGetMetadata(ctx)
	if err != nil {
		return nil, err
	}
	decoder, err := decoder.NewDecoder(l, metadataRaw)
	if err != nil {
		return nil, err
	}

	r := HeadReader{
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

func getMissingValidatorsFrom(groups [][]uint64, votedValidators []uint64) []uint64 {
	if len(votedValidators) == 0 {
		return nil
	}
	for _, members := range groups {
		for _, m := range members {
			// group found
			if m == votedValidators[0] {
				res := []uint64{}
				for _, gm := range members {
					found := false
					for _, vv := range votedValidators {
						if gm == vv {
							found = true
						}
					}
					if !found {
						res = append(res, gm)
					}
				}
				return res

			}
		}
	}
	return nil
}
func (reader *HeadReader) ProcessBlockParaVotes(ctx context.Context, hash string) error {
	var r *decoder.StorageRequest
	r, _ = reader.decoder.NewStorageRequest("paraScheduler", "validatorGroups")
	validatorGroupsRaw, err := reader.wsclient.StateGetStorage(ctx, r, hash)
	if err != nil {
		reader.log.WithError(err).Warn("unable to read storage paraScheduler_validatorGroups")
		return err
	}
	var validatorGroups [][]uint64
	for _, vg := range dto.MustSlice(r.DecodeResponse(validatorGroupsRaw)) {
		group := []uint64{}
		for _, v := range dto.MustSlice(vg) {
			group = append(group, dto.MustInt(v))
		}
		validatorGroups = append(validatorGroups, group)
	}
	r, _ = reader.decoder.NewStorageRequest("paraInherent", "onChainVotes")
	paraVotesRaw, err := reader.wsclient.StateGetStorage(ctx, r, hash)
	if err != nil {
		reader.log.WithError(err).Warn("unable to read storage paraInherent_onChainVotes")
		return err
	}
	paraVotes := r.DecodeResponse(paraVotesRaw)
	if paraVotes == nil {
		reader.log.WithError(err).Warn("unable to decode storage paraInherent_onChainVotes")
		return fmt.Errorf("nil response from DecodeResponse()")
	}
	psValidators := reader.GetParaSessionValidators(ctx, hash, uint32(dto.MustMap(paraVotes).MustInt("session")))
	if paraVotes != nil {
		for _, candidatesVals := range dto.MustMap(paraVotes).GetSlice("backing_validators_per_candidate") {
			// can be used later for para_id breakdown
			//paraId := candidatesVals.Get("col1").Get("descriptor").MustInt("para_id")
			votedValidators := []uint64{}
			for _, groupVotes := range candidatesVals.GetSlice("col2") {
				votedValidators = append(votedValidators, groupVotes.MustInt("col1"))
				// can go deeper and check backable (explicit)/seconded (implicit) statements if need be
			}
			missingVotes := getMissingValidatorsFrom(validatorGroups, votedValidators)
			for _, vv := range votedValidators {
				if reader.registry == nil || reader.GetValidatorsHostname(psValidators[vv]) != "" {
					reader.mon.ProcessEvent(MetricBackingVotesExpectedCount, 1, reader.LabelValues(psValidators[vv])...)
				}
			}
			if len(missingVotes) > 0 {
				for _, mv := range missingVotes {
					if reader.registry == nil || reader.GetValidatorsHostname(psValidators[mv]) != "" {
						reader.mon.ProcessEvent(MetricBackingVotesMissedCount, 1, reader.LabelValues(psValidators[mv])...)
						reader.mon.ProcessEvent(MetricBackingVotesExpectedCount, 1, reader.LabelValues(psValidators[mv])...)
					}
				}
			}
		}
	}
	return nil
}
func (reader *HeadReader) ProcessBlockEvents(ctx context.Context, hash string) error {
	r, _ := reader.decoder.NewStorageRequest("system", "events")
	eventsRaw, err := reader.wsclient.StateGetStorage(ctx, r, hash)
	if err != nil {
		reader.log.WithError(err).Warn("unable to read storage system_events")
		return err
	}
	events := reader.decoder.DecodeEvents(ctx, eventsRaw)
	if events != nil {
		var (
			disputeEvents []dto.Event
		)
		for i := 0; i < len(events); i++ {
			switch {
			case events[i].Type.ModuleId == "ParasDisputes" && events[i].Type.EventId == "DisputeConcluded":
				conclustion := events[i].Params.([]interface{})
				if dto.MustMap(conclustion[1]).MustString("value") == "Valid" {
					disputeEvents = append(disputeEvents, events[i])
				}
			}
			reader.mon.ProcessEvent(MetricChainEventsCount, 1, reader.LabelValues("", events[i].Type.ModuleId, events[i].Type.EventId)...)

		}
		reader.HandleDisputesConcluded(ctx, hash, disputeEvents)
		reader.HandleAllEvents(ctx, hash, events)
		reader.EventsProcessed.Add(int64(len(events)))
	}
	return nil
}

func (reader *HeadReader) subscribeHeadHashes(parentCtx context.Context, hashes chan string) error {
	frames, failures := reader.wsclient.ChainSubscribeNewHead(parentCtx)
	for {
		select {
		case f := <-frames:
			hashes <- dto.MustMap(f.Params).Get("result").MustString("parentHash")
		case e := <-failures:
			return e
		case <-parentCtx.Done():
			return parentCtx.Err()
		}
	}
}

func (reader *HeadReader) pollHeadHashes(parentCtx context.Context, hashes chan string) error {
	ticker := time.NewTicker(15 * time.Second)
	defer ticker.Stop()
	for {
		ctx, cancel := context.WithTimeout(parentCtx, 60*time.Second)
		defer cancel()
		select {
		case <-ticker.C:
			header, err := reader.wsclient.ChainGetHeader(ctx, "")
			if err != nil {
				return err
			}
			if reader.LastProcessedHeight == 0 {
				reader.LastProcessedHeight = header.MustInt("number") - 1
			}
			for i := reader.LastProcessedHeight + 1; i <= header.MustInt("number"); i++ {
				hash, err := reader.wsclient.ChainGetBlockHash(ctx, i)
				if err != nil {
					return err
				}
				hashes <- hash
				reader.LastProcessedHeight = i
			}
		case <-ctx.Done():
			return ctx.Err()
		case <-parentCtx.Done():
			return parentCtx.Err()
		}
		cancel()
	}
}

func (reader *HeadReader) Read(ctx context.Context) error {

	headHashes := make(chan string)
	defer close(headHashes)
	g, ctx := errgroup.WithContext(ctx)

	// liveness ticker
	g.Go(func() error {
		ticker := time.NewTicker(time.Minute)
		defer ticker.Stop()
		reader.EventsRate = 1
		counters := [3]int64{0, 0, 0}
		for {
			select {
			case <-ticker.C:
				counters[0] = counters[1]
				counters[1] = counters[2]
				counters[2] = reader.EventsProcessed.Load()
				reader.EventsRate = (counters[2] - counters[0]) / 3
				reader.log.Infof("exporters average events rate %d/min", reader.EventsRate)
				if reader.EventsRate == 0 {
					return fmt.Errorf("no new events during tick interval")
				}
			case <-ctx.Done():
				return nil
			}

		}
	})
	// follow head goroutine
	g.Go(func() error {
		if reader.cfg.NewHeadBy == "subscription" {
			if err := reader.subscribeHeadHashes(ctx, headHashes); err != nil {
				return err
			} else {
				return nil
			}
		} else {
			if err := reader.pollHeadHashes(ctx, headHashes); err != nil {
				return err
			} else {
				return nil
			}
		}
	})
	// handle input hashes
	g.Go(func() error {
		for {
			select {
			case h := <-headHashes:
				g.Go(func() error {
					ctx, cancel := context.WithTimeout(ctx, 120*time.Second)
					defer cancel()
					if err := reader.ProcessBlockEvents(ctx, h); err != nil {
						return err
					}
					if err := reader.ProcessBlockParaVotes(ctx, h); err != nil {
						return err
					}
					return nil
				})
			case <-ctx.Done():
				return nil
			}
		}
	})
	if err := g.Wait(); err != nil {
		reader.log.WithError(err).Error("process head error")
		return err
	}
	return nil
}

func (reader *HeadReader) HandleDisputesConcluded(ctx context.Context, hash string, events []dto.Event) {
	if len(events) == 0 {
		return
	}
	// event itself does not contain accounts we need to extract extrinsics
	extrinsicIdxs := make(map[int]byte)
	for _, e := range events {
		extrinsicIdxs[e.ExtrinsicIdx] = 1
	}

	block, err := reader.wsclient.ChainGetBlock(ctx, hash)
	if err != nil {
		reader.log.WithField("block", hash).WithError(err).Warn("unable to read block due to transport issues")
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
						accU32 := reader.GetParaSessionValidatorBy(ctx, hash, session, validatorIdx)
						reader.mon.ProcessEvent(MetricChainEventsByAccountCount, 1, reader.LabelValues(accU32, "ParasDisputes", "DisputeConcluded")...)
					}
				}
			}
		}
	}
}

func (reader *HeadReader) HandleAllEvents(ctx context.Context, hash string, events []dto.Event) {
	if len(events) == 0 {
		return
	}
	accsU32 := reader.GetSessionValidators(ctx, hash, 0)
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
					reader.mon.ProcessEvent(MetricChainEventsByAccountCount, 1, reader.LabelValues(accsU32[i], e.Type.ModuleId, e.Type.EventId)...)
					break
				}
			}
		}
	}
}

// TODO: cleanup
func (reader *HeadReader) GetParaSessionValidators(ctx context.Context, hash string, session uint32) []string {
	if _, ok := reader.paraSessionValidators.Load(session); !ok {
		req, _ := reader.decoder.NewStorageRequest("paraSessionInfo", "accountKeys", session)
		resp, err := reader.wsclient.StateGetStorage(ctx, req, hash)
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

func (reader *HeadReader) GetParaSessionValidatorBy(ctx context.Context, hash string, session uint32, idx int) string {

	validators := reader.GetParaSessionValidators(ctx, hash, session)
	if idx > len(validators) {
		return "Unknown"
	}
	return validators[idx]
}

// TODO: cleanup
func (reader *HeadReader) GetSessionValidators(ctx context.Context, hash string, session uint32) []string {
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
		resp, err := reader.wsclient.StateGetStorage(ctx, req, hash)
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

func (reader *HeadReader) GetSessionValidatorBy(ctx context.Context, hash string, session uint32, idx int) string {

	validators := reader.GetSessionValidators(ctx, hash, session)
	if idx > len(validators) {
		return "Unknown"
	}
	return validators[idx]
}

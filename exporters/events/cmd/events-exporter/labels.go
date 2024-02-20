package main

import (
	"context"
	"io"
	"os"
	"path/filepath"
	"substrate-events-exporter/internal/decoder"
	"substrate-events-exporter/internal/dto"
	"substrate-events-exporter/internal/monitoring"
	"time"

	"gopkg.in/yaml.v3"
)

const (
	MetricChainEventsCount          = "polkadot_events"
	MetricChainEventsByAccountCount = "polkadot_events_by_account"
	MetricBackingVotesExpectedCount = "polkadot_pv_backing_votes_expected"
	MetricBackingVotesMissedCount   = "polkadot_pv_backing_votes_missed"
)

func (reader *HeadReader) GetMonitoringEvents() []monitoring.MonitoringEvent {
	extra := []string{}
	if reader.registry != nil {
		extra = append(extra, "node")
	}
	if reader.cfg.ExposeIdentities {
		extra = append(extra, "identity")
	}
	return []monitoring.MonitoringEvent{
		{
			Name:     MetricChainEventsCount,
			TypeName: monitoring.TypeCounter,
			Labels:   []string{"chain", "module", "method"},
		},
		{
			Name:     MetricChainEventsByAccountCount,
			TypeName: monitoring.TypeCounter,
			Labels:   append([]string{"chain", "module", "method", "account"}, extra...),
		},
		{
			Name:     MetricBackingVotesExpectedCount,
			TypeName: monitoring.TypeCounter,
			Labels:   append([]string{"chain", "account"}, extra...),
		},
		{
			Name:     MetricBackingVotesMissedCount,
			TypeName: monitoring.TypeCounter,
			Labels:   append([]string{"chain", "account"}, extra...),
		},
	}
}

func (reader *HeadReader) SetObserver(mon monitoring.Observer) {
	reader.mon = mon
}

func (reader *HeadReader) LabelValues(account string, others ...string) []string {
	var extra []string
	if account != "" {
		extra = []string{reader.decoder.SS58Encode(account)}
		if reader.registry != nil {
			extra = append(extra, reader.GetValidatorsHostname(account))
		}
		if reader.cfg.ExposeIdentities {
			ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
			defer cancel()
			extra = append(extra, reader.GetValidatorsIdentity(ctx, account))
		}
	}
	chain := reader.decoder.ChainSpecName
	if reader.cfg.LabelChainValue != "" {
		chain = reader.cfg.LabelChainValue
	}
	var finalValues []string
	finalValues = append(finalValues, chain)
	if len(others) > 0 {
		finalValues = append(finalValues, others...)
	}
	if len(extra) > 0 {
		finalValues = append(finalValues, extra...)
	}
	return finalValues
}

// Read/Cache validator identity up to super if possible for better grouping
func (reader *HeadReader) GetValidatorsIdentity(ctx context.Context, accU32 string) string {
	var (
		resp string
		err  error
		req  *decoder.StorageRequest
	)

	if id, ok := reader.identities[accU32]; ok {
		return id
	}

	accs := []string{accU32}
	for i := 0; i < len(accs); i++ {
		if req, err = reader.decoder.NewStorageRequest("identity", "superOf", accs[i]); err != nil {
			return ""
		}
		if resp, err = reader.wsclient.StateGetStorage(ctx, req, ""); err != nil {
			return ""
		}
		idTuple := req.DecodeResponse(resp)
		parentAcc := dto.MustMap(idTuple).MustString("col1")
		if parentAcc != "" {
			accs = append(accs, parentAcc)
			if _, ok := reader.identities[parentAcc]; ok {
				break
			}
		}
	}

	var id string
	for i := len(accs) - 1; i >= 0; i-- {
		if v, ok := reader.identities[accs[i]]; ok && v != "" {
			id = v
			continue
		}
		if id == "" {
			if req, err = reader.decoder.NewStorageRequest("identity", "identityOf", accs[i]); err != nil {
				return ""
			}
			if resp, err = reader.wsclient.StateGetStorage(ctx, req, ""); err != nil {
				return ""
			}
			identity := req.DecodeResponse(resp)
			for _, val := range dto.MustMap(identity).Get("info").MustStringMap("display") {
				if val != "" {
					id = val
				}
			}
			for _, val := range dto.MustMap(identity).Get("info").MustStringMap("email") {
				if val != "" {
					id = val
				}
			}
			for _, val := range dto.MustMap(identity).Get("info").MustStringMap("legal") {
				if val != "" {
					id = val
				}
			}
		}
		reader.identities[accs[i]] = id
	}

	return id
}

func (reader *HeadReader) ReadKnownValidatorsFile(filename string) {
	if filename != "" {
		fi, err := os.Lstat(filename)
		if err != nil {
			reader.log.WithError(err).Errorf("loading known validators skipped %s", filename)
			return
		}
		if fi.Mode()&os.ModeSymlink != 0 {
			filename, _ = os.Readlink(filename)
		}
		pth, err := filepath.Abs(filename)
		if err != nil {
			reader.log.WithError(err).Errorf("loading known validators skipped %s", pth)
			return
		}

		if r, err := os.Open(pth); err != nil {
			reader.log.WithError(err).Errorf("loading known validators skipped %s", pth)
			return
		} else {
			payload, err := io.ReadAll(r)
			if err != nil {
				reader.log.WithError(err).Errorf("loading known validators skipped %s", pth)
				return
			}
			registry := ValidatorsRegistry{}
			if err := yaml.Unmarshal(payload, &registry); err != nil {
				reader.log.WithError(err).Errorf("loading known validators skipped %s", pth)
				return
			}
			reader.registry = &registry
		}
	}
}

func (reader *HeadReader) GetValidatorsHostname(accU32 string) string {
	if reader.registry == nil {
		return ""
	}

	accSS58 := reader.decoder.SS58Encode(accU32)
	for name, validator := range reader.registry.Validators {
		if validator.AccountSS58 == accSS58 {
			return name
		}
	}
	return ""
}

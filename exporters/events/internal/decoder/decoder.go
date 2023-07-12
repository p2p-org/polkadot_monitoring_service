package decoder

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"substrate-events-exporter/internal/dto"

	scale "github.com/itering/scale.go"
	"github.com/itering/scale.go/types"
	"github.com/itering/scale.go/types/scaleBytes"
	"github.com/itering/scale.go/utiles"
	"github.com/sirupsen/logrus"
	"github.com/vedhavyas/go-subkey/v2"
)

type Decoder struct {
	log           *logrus.Logger
	metadata      *types.MetadataStruct
	ss58Prefix    uint16
	ChainSpecName string
}

func NewDecoder(l *logrus.Logger, metadata string) (*Decoder, error) {
	d := Decoder{
		log: l,
	}
	var err error

	meta := &scale.MetadataDecoder{}
	meta.Init(utiles.HexToBytes(metadata))
	err = meta.Process()
	if err != nil {
		return nil, err
	}
	d.metadata = &meta.Metadata
	for _, c := range d.metadata.Metadata.Modules[0].Constants {
		if c.Name == "SS58Prefix" {
			scale := types.ScaleDecoder{}
			scale.Init(scaleBytes.ScaleBytes{Data: utiles.HexToBytes(c.ConstantsValue)}, nil)
			d.ss58Prefix = scale.ProcessAndUpdateData(c.Type).(uint16)
		}
		if c.Name == "Version" {
			scale := types.ScaleDecoder{}
			scale.Init(scaleBytes.ScaleBytes{Data: utiles.HexToBytes(c.ConstantsValue)}, nil)
			d.ChainSpecName = dto.MustMap(scale.ProcessAndUpdateData(c.Type)).MustString("spec_name")
		}
	}
	//d.scaleOpts = &types.ScaleDecoderOption{Metadata: &meta.Metadata}
	return &d, nil
}

func (d *Decoder) DecodeEvents(ctx context.Context, payload string) []dto.Event {
	decoder := scale.EventsDecoder{}
	defer func() {
		if r := recover(); r != nil {
			d.log.Warn(r)
		}
	}()
	decoder.Init(scaleBytes.ScaleBytes{Data: utiles.HexToBytes(payload)}, &types.ScaleDecoderOption{Metadata: d.metadata})
	decoder.Process()

	switch v := decoder.Value.(type) {
	case []interface{}:
		var events []dto.Event
		for _, eventRecord := range v {

			e := eventRecord.(map[string]interface{})
			b, _ := json.Marshal(e["params"])
			var p interface{}
			json.Unmarshal(b, &p)
			events = append(events, dto.Event{
				Type: dto.EventType{
					ModuleId: e["module_id"].(string),
					EventId:  e["event_id"].(string),
				},
				ExtrinsicIdx: e["extrinsic_idx"].(int),
				Params:       p,
			})
			//d.log.Debugf("decoded new event %v", events[len(events)-1].Type)
		}
		return events
	default:
		return nil
	}
}
func (d *Decoder) SS58Encode(pubkey string) string {
	return subkey.SS58Encode(utiles.HexToBytes(pubkey), d.ss58Prefix)
}

func (d *Decoder) SS58Decode(pubkey string) string {

	_, result, _ := subkey.SS58Decode(pubkey)
	return fmt.Sprintf("0x%s", utiles.BytesToHex(result))
}

type StorageRequest struct {
	Module     string
	Method     string
	StorageKey string
	StoredType string
}

// Works only with Metadata V14
func (d *Decoder) NewStorageRequest(module, method string, args ...interface{}) (*StorageRequest, error) {
	var sc StorageRequest
	for _, runtimeModule := range d.metadata.Metadata.Modules {
		if strings.EqualFold(runtimeModule.Name, module) {
			for _, runtimeMethod := range runtimeModule.Storage {
				if strings.EqualFold(runtimeMethod.Name, method) {
					sc.Module = runtimeModule.Name
					sc.Method = runtimeMethod.Name
					storageKey := append(TwoxHash([]byte(sc.Module), 128), TwoxHash([]byte(sc.Method), 128)...)
					switch t := runtimeMethod.Type; t.Origin {
					// args must be same as keyVec
					case "Map":
						sc.StoredType = t.NMapType.Value
						argCount := 0
						if len(args) <= len(t.NMapType.KeyVec) {
							argCount = len(args)
						} else {
							return nil, fmt.Errorf("too many arguments for %s.%s", sc.Module, sc.Method)
						}
						for i := 0; i < argCount; i++ {
							arg := types.Encode(t.NMapType.KeyVec[i], args[i])
							storageKey = append(storageKey, DoHash(utiles.HexToBytes(arg), t.NMapType.Hashers[i])...)
						}
					// no args, only response
					case "PlainType":
						sc.StoredType = *t.PlainType
					}
					sc.StorageKey = fmt.Sprintf("0x%s", utiles.BytesToHex(storageKey))
					return &sc, nil
				}
			}
		}
	}
	return nil, fmt.Errorf("storage request %s.%s not found in runtime", module, method)
}

func (r *StorageRequest) DecodeResponse(payload string) dto.Params {
	scale := types.ScaleDecoder{}
	defer func() {
		if rec := recover(); rec != nil {
			return
		}
	}()
	scale.Init(scaleBytes.ScaleBytes{Data: utiles.HexToBytes(payload)}, nil)
	return scale.ProcessAndUpdateData(r.StoredType)
}

func (d *Decoder) DecodeExtrinsic(ctx context.Context, payload string) dto.Mapped {
	decoder := scale.ExtrinsicDecoder{}
	defer func() {
		if r := recover(); r != nil {
			d.log.Warn(r)
		}
	}()

	decoder.Init(scaleBytes.ScaleBytes{Data: utiles.HexToBytes(payload)}, &types.ScaleDecoderOption{Metadata: d.metadata})
	decoder.Process()
	if b, err := json.Marshal(decoder.Value); err == nil {
		var result dto.Mapped
		json.Unmarshal(b, &result)
		return result
	}
	return nil
}

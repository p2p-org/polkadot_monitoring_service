package client

import (
	"context"
	"encoding/json"
	"fmt"
	"math/rand"
	"substrate-events-exporter/internal/dto"
	"sync"

	"github.com/sirupsen/logrus"
	"nhooyr.io/websocket"
)

type WSMessageBroker struct {
	//in            chan *WSMessageBrokerFrame
	log           *logrus.Logger
	requests      sync.Map // map[int]chan *WSMessageBrokerFrame
	subscriptions sync.Map // map[string]chan *WSMessageBrokerFrame
	ws            *websocket.Conn
	ctx           context.Context
	err           error
}

type WSMessageBrokerFrame struct {
	Frame *dto.RPCFrame
	Error error
	ctx   context.Context
}

func NewWSMessageBroker(ctx context.Context, log *logrus.Logger, conn *websocket.Conn) *WSMessageBroker {
	broker := WSMessageBroker{
		log: log,
		ctx: ctx,
		ws:  conn,
	}

	go func() {
		broker.err = broker.readContinuously(ctx)
	}()
	return &broker
}

// Simple request wihtout need to watch server-side pushes
func (broker *WSMessageBroker) WSRequest(ctx context.Context, req *dto.RPCFrame) (*dto.RPCFrame, error) {
	ch, err := broker.submit(ctx, req, false)
	if err != nil {
		return nil, err
	}
	select {
	case brokerResp := <-ch:
		if brokerResp.Error == nil {
			return brokerResp.Frame, nil
		} else {
			return nil, brokerResp.Error
		}
	case <-ctx.Done():
		return nil, fmt.Errorf("error %v during reques: %s", ctx.Err(), req.Raw)
	}

}

// Submit and subscribe on server pushes
func (broker *WSMessageBroker) Subscribe(ctx context.Context, req *dto.RPCFrame) (chan *dto.RPCFrame, chan error) {
	r := make(chan *dto.RPCFrame)
	e := make(chan error, 1)
	ch, err := broker.submit(ctx, req, true)
	if err != nil {
		e <- err
		return nil, e
	}

	go func() {
		defer close(r)
		defer close(e)
		for frame := range ch {
			ctx = frame.ctx
			if frame.Error != nil {
				e <- frame.Error
				return
			}
			r <- frame.Frame
		}
	}()
	return r, e
}

func (broker *WSMessageBroker) submit(ctx context.Context, frame *dto.RPCFrame, isSubscription bool) (chan *WSMessageBrokerFrame, error) {
	frame.RPC = "2.0"
	if frame.Id == 0 {
		frame.Id = 1 + rand.Intn(29999)
	}
	if frame.Params == nil {
		frame.Params = []string{}
	}
	payload, err := json.Marshal(frame)
	if err != nil {
		return nil, err
	}
	err = broker.ws.Write(ctx, websocket.MessageText, payload)
	if err != nil {
		return nil, err
	}
	var ch chan *WSMessageBrokerFrame
	if isSubscription {
		broker.log.Debugf("new subscription id: %d, method %s", frame.Id, frame.Method)
		ch = make(chan *WSMessageBrokerFrame)
		broker.subscriptions.Store(subscriptionInitKey(frame.Id), ch)
	} else {
		broker.log.Debugf("new request id: %d, method %s", frame.Id, frame.Method)
		ch = make(chan *WSMessageBrokerFrame, 1)
		broker.requests.Store(frame.Id, ch)
	}
	return ch, nil
}

// Temporary key to init subscription
func subscriptionInitKey(frameId int) string {
	return fmt.Sprintf("init/%d", frameId)
}

func (broker *WSMessageBroker) cleanup() {
	broker.requests.Range(func(k, v interface{}) bool {
		ch := v.(chan *WSMessageBrokerFrame)
		ch <- &WSMessageBrokerFrame{
			Frame: &dto.RPCFrame{},
			Error: broker.err,
		}
		close(ch)
		return true
	})
	broker.subscriptions.Range(func(k, v interface{}) bool {
		ch := v.(chan *WSMessageBrokerFrame)
		ch <- &WSMessageBrokerFrame{
			Frame: &dto.RPCFrame{},
			Error: broker.err,
		}
		close(ch)
		return true
	})
}

func (broker *WSMessageBroker) readContinuously(ctx context.Context) error {
	// read loop
	read := make(chan *WSMessageBrokerFrame)
	defer broker.cleanup()
	go func(ctx context.Context, read chan *WSMessageBrokerFrame) {
		defer close(read)
		for {
			var (
				err error
				buf []byte
			)
			if ctx.Err() != nil {
				return
			}
			if _, buf, err = broker.ws.Read(ctx); err != nil {
				read <- &WSMessageBrokerFrame{
					ctx:   ctx,
					Frame: nil,
					Error: err,
				}
				continue
			}
			var f dto.RPCFrame
			if err = json.Unmarshal(buf, &f); err != nil {
				broker.log.WithError(err).Errorf("failed to parse server-side frame %s", string(buf))
				continue
			}
			read <- &WSMessageBrokerFrame{
				ctx:   context.WithValue(ctx, ContextKeyRPCCallId, f.Id),
				Frame: &f,
				Error: nil,
			}
		}
	}(ctx, read)

	for {
		select {
		case frame := <-read:
			// frame not read
			if frame.Error != nil {
				// read loop or pinger error -> stop processing
				return frame.Error
			}
			//var resp *WSMessageBrokerFrame
			// server-side subscription push does not contain Id
			if frame.Frame.Id == 0 {
				pushParams := dto.MustMap(frame.Frame.Params)
				subscriptionID := pushParams.MustString("subscription")
				if ch, ok := broker.subscriptions.Load(subscriptionID); ok {
					ch := ch.(chan *WSMessageBrokerFrame)
					ch <- &WSMessageBrokerFrame{
						Error: frame.Error,
						Frame: frame.Frame,
					}
				} else {
					broker.log.Warnf("no response channel found for subscription %s", subscriptionID)
				}
			} else {
				// move subscription from init/123 to it's place
				if ch, initExists := broker.subscriptions.LoadAndDelete(subscriptionInitKey(frame.Frame.Id)); initExists {
					subscriptionId := frame.Frame.StringResult()
					broker.subscriptions.Store(subscriptionId, ch)
				} else {
					if ch, ok := broker.requests.LoadAndDelete(frame.Frame.Id); ok {
						ch := ch.(chan *WSMessageBrokerFrame)
						ch <- &WSMessageBrokerFrame{
							Error: frame.Error,
							Frame: frame.Frame,
						}
					}
				}
			}
		case <-ctx.Done():
			return ctx.Err()
		}
	}
}

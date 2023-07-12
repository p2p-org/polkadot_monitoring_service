package client

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"substrate-events-exporter/internal/decoder"
	"substrate-events-exporter/internal/dto"
	"sync"
	"time"

	"github.com/sirupsen/logrus"
	"nhooyr.io/websocket"
)

type contextKey string

const (
	ContextKeyRPCCallId  = contextKey("wsconnRequestID")
	ContextKeyBrokerName = contextKey("wsconnID")
)

type RPCClient struct {
	endpoint          string
	clientTimeout     time.Duration
	log               *logrus.Logger
	defaultConnection string
	connections       sync.Map //map[string]*WSMessageBroker
	rw                sync.Mutex
}

func NewRPCClient(log *logrus.Logger, endpoint string) *RPCClient {
	c := RPCClient{
		endpoint:          endpoint,
		clientTimeout:     60 * time.Second,
		log:               log,
		defaultConnection: "default",
	}
	return &c
}

func (w *RPCClient) StateGetMetadata(ctx context.Context) (string, error) {
	conn, err := w.GetOrCreateConnection(ctx)
	if err != nil {
		return "", err
	}
	if resp, err := conn.WSRequest(ctx, &dto.RPCFrame{Method: "state_getMetadata"}); err == nil {
		return resp.StringResult(), nil
	} else {
		return "", err
	}
}

func (w *RPCClient) ChainGetBlock(ctx context.Context, hash string) (*dto.Block, error) {

	var (
		resp *dto.RPCFrame
		err  error
	)
	conn, err := w.GetOrCreateConnection(ctx)
	if err != nil {
		return nil, err
	}
	resp, err = conn.WSRequest(ctx, &dto.RPCFrame{Method: "chain_getBlock", Params: []string{hash}})
	if err != nil {
		return nil, err
	}
	if resp.Error != nil {
		return nil, fmt.Errorf("%v", resp.Error)
	}
	b := dto.Block{
		Number:     resp.MappedResult().Get("block").Get("header").MustInt("number"),
		ParentHash: resp.MappedResult().Get("block").Get("header").MustString("parentHash"),
		Extrinsics: resp.MappedResult().Get("block").MustStrings("extrinsics"),
		Hash:       hash,
	}
	return &b, nil
}

func (w *RPCClient) ChainGetHeader(ctx context.Context, hash string) (dto.Mapped, error) {
	conn, err := w.GetOrCreateConnection(ctx)
	if err != nil {
		return nil, err
	}

	var params []string
	if hash != "" {
		params = []string{hash}
	}
	if resp, err := conn.WSRequest(ctx, &dto.RPCFrame{Method: "chain_getHeader", Params: params}); err == nil {
		return resp.MappedResult(), err
	} else {
		return dto.Mapped{}, err
	}
}

func (w *RPCClient) ChainGetBlockHash(ctx context.Context, num uint64) (string, error) {
	conn, err := w.GetOrCreateConnection(ctx)
	if err != nil {
		return "", err
	}
	if v, err := conn.WSRequest(ctx, &dto.RPCFrame{Method: "chain_getBlockHash", Params: []uint64{num}}); err == nil {
		return v.StringResult(), nil
	} else {
		return "", err
	}
}

func (w *RPCClient) StateGetStorage(ctx context.Context, request *decoder.StorageRequest, blockHash string) (string, error) {
	var params []string
	if blockHash != "" {
		params = []string{request.StorageKey, blockHash}
	} else {
		params = []string{request.StorageKey}
	}
	conn, err := w.GetOrCreateConnection(ctx)
	if err != nil {
		return "", err
	}
	if v, err := conn.WSRequest(ctx, &dto.RPCFrame{Method: "state_getStorage", Params: params}); err == nil { // panic
		return v.StringResult(), nil
	} else {
		return "", err
	}
}

func (w *RPCClient) ChainSubscribeNewHead(ctx context.Context) (chan *dto.RPCFrame, chan error) {
	conn, err := w.GetOrCreateConnection(ctx)
	if err != nil {
		e := make(chan error, 1)
		e <- err
		return nil, e
	}
	return conn.Subscribe(ctx, &dto.RPCFrame{Method: "chain_subscribeNewHead"})
}

// Returns context that can be used later for RPC requests
func (w *RPCClient) NewConnectionContext(ctx context.Context, name string) context.Context {
	return context.WithValue(ctx, ContextKeyBrokerName, name)
}

func (w *RPCClient) ReleaseConnection(ctx context.Context) {
	var name string
	if ctx.Value(ContextKeyBrokerName) == nil {
		ctx = context.WithValue(ctx, ContextKeyBrokerName, w.defaultConnection)
	}
	w.rw.Lock()
	defer w.rw.Unlock()
	name = ctx.Value(ContextKeyBrokerName).(string)
	if conn, ok := w.connections.LoadAndDelete(name); ok {
		conn := conn.(*WSMessageBroker)
		w.closeWSConnection(conn.ws, conn.err)
	}
}

func (w *RPCClient) GetOrCreateConnection(ctx context.Context) (*WSMessageBroker, error) {
	var name string
	if ctx.Value(ContextKeyBrokerName) == nil {
		ctx = context.WithValue(ctx, ContextKeyBrokerName, w.defaultConnection)
	}
	name = ctx.Value(ContextKeyBrokerName).(string)

	w.rw.Lock()
	defer w.rw.Unlock()
	if conn, ok := w.connections.Load(name); ok {
		conn := conn.(*WSMessageBroker)
		if conn.err == nil {
			return conn, nil
		}
		// get original context
		ctx = conn.ctx
		// reset exsiting connection in case of errors
		w.log.WithError(conn.err).Warnf("connection [%s] has failed and will be recreated", name)
		w.closeWSConnection(conn.ws, conn.err)
		w.connections.Delete(name)
	}

	c, err := w.openWSConnection(ctx, "")
	if err != nil {
		return nil, err
	}

	conn := NewWSMessageBroker(ctx, w.log, c)
	w.connections.Store(name, conn)
	return conn, nil
}

func (w *RPCClient) openWSConnection(ctx context.Context, server string) (*websocket.Conn, error) {
	if server == "" {
		server = w.endpoint
	}
	c, _, err := websocket.Dial(ctx, server, &websocket.DialOptions{
		HTTPClient: &http.Client{
			Timeout: w.clientTimeout,
			Transport: &http.Transport{
				MaxIdleConnsPerHost: 1,
				IdleConnTimeout:     3 * w.clientTimeout,
			},
		},
	})
	if err != nil {
		return nil, err
	}

	c.SetReadLimit(15 * 1024 * 1024)
	return c, nil
}

func (w *RPCClient) closeWSConnection(c *websocket.Conn, err error) {
	if err != nil {
		w.log.WithError(err).Debug("unexpected WS session termination")
	}
	defer c.Close(websocket.StatusInternalError, "")
	err = c.Close(websocket.StatusNormalClosure, "")
	if errors.Is(err, context.Canceled) {
		return
	}
	if websocket.CloseStatus(err) == websocket.StatusNormalClosure ||
		websocket.CloseStatus(err) == websocket.StatusGoingAway {
		return
	}
}

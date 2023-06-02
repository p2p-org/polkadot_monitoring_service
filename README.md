# Polkadot monitoring service

1. Install Docker and Docker Compose from https://docs.docker.com/engine/install/
2. Create `polkadot.env` and `kusama.env` and set:

```jsx
WS_ENDPOINT="ws://your-node1:9944"
RPC_ENDPOINTS="[http://your-node1:9933](http://your-node1:9933/),[http://your-node2:9933](http://your-node2:9933/),[http://your-node3:9933](http://your-node3:9933/)"
```

1. Run `docker-compose -f docker-compose.yml -f polkadot.yml -f kusama.yml up -d`
2. Check your live dashboard at http://127.0.0.1:3000/d/fDrj0_EGz/p2p-org-polkadot-kusama-dashboard?orgId=1 (admin/admin)

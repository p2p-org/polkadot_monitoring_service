run:
	docker-compose -f docker-compose.yml -f kusama.yml -f polkadot.yml up

polkadot:
	docker-compose -f docker-compose.yml -f polkadot.yml up

kusama:
	docker-compose -f docker-compose.yml -f kusama.yml up

clean:
	docker-compose -f docker-compose.yml -f kusama.yml -f polkadot.yml down -v
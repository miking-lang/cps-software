.PHONY: test-docker

IMAGENAME = mikinglang/remote-ctrl-server
VERSION = 0.0.1-dev

build-docker:
	docker build --tag "$(IMAGENAME):$(VERSION)" \
	             --force-rm \
	             --progress=plain \
	             --file Dockerfile \
	             ../..

run-docker:
	$(eval DOCKERNAME := remote-ctrl-server)
	docker run --rm -it \
	       --hostname "$(DOCKERNAME)" \
	       --name "$(DOCKERNAME)" \
	       --privileged \
	       --publish 8372:8372 \
	       "$(IMAGENAME):$(VERSION)" bash

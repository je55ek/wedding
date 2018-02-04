BUILDDIR=build
VERSION := $(shell git describe --long --dirty)
ZIPNAME := wedding-app-$(VERSION).zip

packages:
	mkdir -p $(BUILDDIR)
	pip install ../ -t $(BUILDDIR) --no-compile
	cd $(BUILDDIR); rm -r *.egg-info; rm -r *.dist-info; cd ../

all: packages
	cp app.py $(BUILDDIR)/; \
		cd $(BUILDDIR); \
		zip -r $(ZIPNAME) ./*; \
		cd ../ ;\
		mv $(BUILDDIR)/$(ZIPNAME) ./

clean:
	rm -rf $(BUILDDIR)

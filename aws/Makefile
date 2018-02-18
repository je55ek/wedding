BUILDDIR := build
VERSION := $(shell git describe --long --dirty --always)
ZIPNAME := wedding-app-$(VERSION).zip
CODE_BUCKET := flyingj-code-dev
RESOURCE_BUCKET := flyingj-wedding
RESOURCES := resources
CLOUDFORMATION_TEMPLATE := template.yaml
STACK_NAME := wedding
AWS_TAGS := "project=wedding"

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

static:
	aws s3 cp --recursive $(RESOURCES) s3://$(RESOURCE_BUCKET)/

deploy: clean all static
	aws s3 mv $(ZIPNAME) s3://$(CODE_BUCKET)/$(ZIPNAME); \
  aws cloudformation deploy \
    --template-file $(CLOUDFORMATION_TEMPLATE) \
    --stack-name $(STACK_NAME) \
    --tags $(AWS_TAGS) \
    --parameter-overrides "CodeKey=$(ZIPNAME)" "CodeBucket=$(CODE_BUCKET)" \
    --capabilities CAPABILITY_NAMED_IAM

clean:
	rm -rf $(BUILDDIR)

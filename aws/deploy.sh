#!/usr/bin/env bash
aws cloudformation deploy \
    --template-file template.yaml \
    --stack-name wedding \
    --tags "environment=dev" "project=wedding" \
    --parameter-overrides "CodeKey=wedding-app-v0.1.1-0-ga34f99e.zip" \
    --capabilities CAPABILITY_NAMED_IAM

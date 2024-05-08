#!/usr/bin/env bash

saveenv=$-
set -e

# install_designate_tempest_plugin
function install_designate_tempest_plugin {
    setup_dev_lib "designate-tempest-plugin"
}

function _configure_tempest {
    if [ -n "$DESIGNATE_BIN_DIR" ]; then
        iniset $TEMPEST_CONFIG dns_feature_enabled designate_manage_path ${DESIGNATE_BIN_DIR}/designate-manage
    fi

    POOLS_YAML_PATH=/etc/designate/multiple-pools.yaml
    cp /etc/designate/pools.yaml ${POOLS_YAML_PATH}
    sed -i 's/"pool_level": "secondary"/"pool_level": "tertiary"/' ${POOLS_YAML_PATH}
}

if [[ "$1" == "stack" ]]; then
    case "$2" in
        install)
            # Install dev library if the user explicitly requests it
            # (INSTALL_TEMPEST=True)
            if [[ "$(trueorfalse False INSTALL_TEMPEST)" == "True" ]]; then
                echo_summary "Installing designate-tempest-plugin"
                install_designate_tempest_plugin
            fi
            ;;
        test-config)
            echo_summary "Configuring tempest designate-manage"
            _configure_tempest
            ;;
    esac
fi

if [[ $saveenv =~ e ]]; then
    set -e
else
    set +e
fi

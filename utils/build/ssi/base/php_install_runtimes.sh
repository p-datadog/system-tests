#!/bin/bash

export PHP_VERSION=$1

if [ -f /etc/debian_version ] || [ "$DISTRIBUTION" = "Debian" ] || [ "$DISTRIBUTION" = "Ubuntu" ]; then
    OS="Debian"
elif [ -f /etc/redhat-release ] || [ "$DISTRIBUTION" = "RedHat" ] || [ "$DISTRIBUTION" = "CentOS" ] || [ "$DISTRIBUTION" = "Amazon" ] || [ "$DISTRIBUTION" = "Rocky" ] || [ "$DISTRIBUTION" = "AlmaLinux" ]; then
    OS="RedHat"
elif [ -f /etc/system-release ] || [ "$DISTRIBUTION" = "Amazon" ]; then
    OS="RedHat"
elif [ -f /etc/Eos-release ] || [ "$DISTRIBUTION" = "Arista" ]; then
    OS="RedHat"
elif [ -f /etc/SuSE-release ] || [ "$DISTRIBUTION" = "SUSE" ] || [ "$DISTRIBUTION" = "openSUSE" ]; then
    OS="SUSE"
elif [ -f /etc/alpine-release ]; then
    OS="Alpine"
fi

if [ "$OS" = "Debian" ]; then
    export DEBIAN_FRONTEND=noninteractive

    # Remove the PHP installed in install_os_deps.sh
    apt remove --yes php-cli
    apt autoremove --yes

    # FIXME: Debian
    #curl -sSL https://packages.sury.org/php/README.txt | sudo bash -x

    # Ubuntu
    LC_ALL=C.UTF-8 add-apt-repository ppa:ondrej/php
    apt update

    apt install --yes "php${PHP_VERSION}-cli"

    php -v

elif [ "$OS" = "RedHat" ]; then
    yum install -y php
else
    echo "Unknown OS"
    exit 1
fi
